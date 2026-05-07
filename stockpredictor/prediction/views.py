from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm, ForgotPasswordForm, WatchlistForm, StockPredictionForm, UserUpdateForm, ProfileUpdateForm
from .models import StockPrediction, StockInfo, MLModelInfo, PredictionLog, Watchlist
from prediction.models import Profile
from django.core.paginator import Paginator
from .utils import predict_stock_trend, fetch_stock_data, fetch_quote, fetch_sparkline
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.timezone import now
import csv
import math, datetime as dt, json, traceback
import yfinance as yf
from django.conf import settings

# Get custom user model
from django.contrib.auth import get_user_model
User = get_user_model()


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'auth/login.html')


def signup_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        confirm = request.POST['confirm']
        if password != confirm:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
        else:
            user = User.objects.create_user(email=email, password=password)
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('user_dashboard')
    return render(request, 'auth/signup.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                messages.success(request, 'Password reset link sent (demo only).')
            else:
                messages.error(request, 'Email not found')
    else:
        form = ForgotPasswordForm()
    return render(request, 'auth/password_reset.html', {'form': form})


@login_required
def user_dashboard(request):
    recent = StockPrediction.objects.filter(user=request.user).order_by('-predicted_on')[:5]
    preview = Watchlist.objects.filter(user=request.user).order_by("-pinned", "symbol")[:3]
    form = StockPredictionForm()
    return render(request, 'user/user_dashboard.html', {
        'form': form,
        'recent_predictions': recent,
        "watchlist_preview": preview,
    })


@login_required
def profile_settings(request):
    if request.method == "POST":
        uform = UserUpdateForm(request.POST, instance=request.user)
        pform = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        uform = UserUpdateForm(instance=request.user)
        pform = ProfileUpdateForm(instance=request.user.profile)
    return render(request, "auth/profile_settings.html", {"uform": uform, "pform": pform})


@login_required
def stock_prediction_view(request):
    result = None
    if request.method == 'POST':
        form = StockPredictionForm(request.POST)
        if form.is_valid():
            prediction = form.save(commit=False)
            prediction.user = request.user

            # Import ML libraries only when needed to save memory
            from .utils import predict_stock_trend
            result = predict_stock_trend(
                prediction.symbol,
                prediction.start_date,
                prediction.end_date
            )
            print("DEBUG prediction result:", result)

            if isinstance(result, dict) and 'error' in result:
                messages.error(request, f"Prediction failed: {result['error']}")
                prediction.trend = 'ERROR'
                prediction.confidence_score = 0.0
            elif isinstance(result, dict):
                prediction.trend = result.get('trend', 'UNKNOWN')
                prediction.confidence_score = float(result.get('confidence', 0.0))
            else:
                messages.error(request, "Unexpected model output.")
                prediction.trend = 'UNKNOWN'
                prediction.confidence_score = 0.0

            prediction.save()

            active_model = MLModelInfo.objects.filter(active=True).first()
            PredictionLog.objects.create(
                user=request.user,
                stock_symbol=prediction.symbol,
                used_model=active_model
            )
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = StockPredictionForm()

    return render(request, 'user/stock_predict.html', {
        'form': form,
        'result': result
    })


@login_required
def prediction_history(request):
    predictions = StockPrediction.objects.filter(user=request.user).order_by('-predicted_on')
    paginator = Paginator(predictions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/prediction_history.html', {
        'page_obj': page_obj,
        "predictions": predictions
    })


def stock_data(request, symbol):
    try:
        period = request.GET.get("period", None)
        interval = request.GET.get("interval", "1d")
        start = request.GET.get("start", None)
        end = request.GET.get("end", None)

        if start and end:
            data = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=True)
        elif period:
            data = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
        else:
            data = yf.download(symbol, period="6mo", interval=interval, auto_adjust=True)

        if data.empty:
            return JsonResponse({"error": f"No data found for symbol {symbol}"}, status=404)

        columns = ['Open', 'High', 'Low', 'Close']
        response = {"dates": data.index.strftime("%Y-%m-%d").tolist()}
        for col in columns:
            if col in data.columns:
                response[col.lower()] = data[[col]].squeeze().tolist()
            else:
                response[col.lower()] = []
        response["trend"] = data["Close"].squeeze().round(2).tolist()
        return JsonResponse(response)

    except Exception as e:
        print("ERROR in stock_data:", e)
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


def _pct(a, b):
    try:
        if a in (None, 0) or b is None:
            return None
        return round((b - a) * 100.0 / a, 2)
    except Exception:
        return None


def stock_info_api(request, symbol):
    sym = symbol.upper().strip()
    try:
        t = yf.Ticker(sym)
        info = t.fast_info or {}

        prev_close = float(info.get("previous_close") or 0) or None
        curr = info.get("last_price") or info.get("last_close") or prev_close
        curr = float(curr) if curr else None

        mcap = info.get("market_cap")
        pe = info.get("trailing_pe") or info.get("pe_ratio")
        dy = info.get("dividend_yield")

        if not mcap or not pe or dy is None:
            try:
                ii = t.info
                mcap = mcap or ii.get("marketCap")
                pe = pe or ii.get("trailingPE")
                if dy is None:
                    dy = ii.get("dividendYield")
            except Exception:
                pass

        if dy is not None:
            dy = round(dy * 100.0, 2) if dy < 1 else round(dy, 2)

        r3y = None
        hist = t.history(period="3y", interval="1d", auto_adjust=True)
        if not hist.empty:
            first = float(hist["Close"].dropna().iloc[0])
            last = float(hist["Close"].dropna().iloc[-1])
            r3y = _pct(first, last)

        chg_1d = _pct(prev_close, curr)

        ii = getattr(t, "info", {}) or {}
        name = ii.get("longName") or sym
        sector = ii.get("sector")

        si, _ = StockInfo.objects.get_or_create(symbol=sym)
        si.full_name = name
        si.sector = sector
        si.market_cap = mcap
        si.previous_close = prev_close
        si.current_price = curr
        si.dividend_yield = dy
        si.pe_ratio = pe
        si.save()

        return JsonResponse({
            "symbol": sym,
            "name": name,
            "sector": sector or "-",
            "market_cap": mcap,
            "previous_close": prev_close,
            "current_price": curr,
            "dividend_yield": dy,
            "pe_ratio": pe,
            "updated_on": now().strftime("%Y-%m-%d %H:%M"),
            "return_3y": r3y,
            "change_1d": chg_1d,
            "tags": ["Equity", "Largecap"]
        })
    except Exception as e:
        print("stock_info ERR:", e)
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def watchlist_view(request):
    form = WatchlistForm()
    items = Watchlist.objects.filter(user=request.user).order_by("-pinned", "symbol")
    return render(request, "user/watchlist.html", {"form": form, "items": items})


@login_required
def watchlist_add(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    form = WatchlistForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    exists = Watchlist.objects.filter(
        user=request.user,
        symbol=form.cleaned_data["symbol"].upper(),
        exchange=(form.cleaned_data.get("exchange") or "NS").upper(),
    ).exists()
    if exists:
        return JsonResponse({"ok": False, "message": "Already in watchlist"}, status=409)

    item = form.save(commit=False)
    item.user = request.user

    q = fetch_quote(item.symbol, item.exchange or "NS")
    if q:
        item.last_price = q["price"]
        item.change_pct = q["change_pct"]
        item.display_name = q["name"]
        item.last_updated = q["ts"]

    item.save()
    return JsonResponse({
        "ok": True,
        "id": item.id,
        "symbol": item.symbol,
        "exchange": item.exchange or "NS",
        "name": item.display_name or item.symbol,
        "price": item.last_price,
        "change_pct": item.change_pct,
        "pinned": item.pinned,
        "group": item.group or "",
        "notes": item.notes or "",
    })


@login_required
def watchlist_remove(request, pk):
    item = get_object_or_404(Watchlist, pk=pk, user=request.user)
    item.delete()
    return JsonResponse({"ok": True})


@login_required
def watchlist_toggle_pin(request, pk):
    item = get_object_or_404(Watchlist, pk=pk, user=request.user)
    item.pinned = not item.pinned
    item.save(update_fields=["pinned"])
    return JsonResponse({"ok": True, "pinned": item.pinned})


@login_required
def watchlist_update_item(request, pk):
    item = get_object_or_404(Watchlist, pk=pk, user=request.user)
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    for key in ["notes", "group", "target_above", "target_below"]:
        if key in request.POST:
            val = request.POST.get(key)
            if key in ("target_above", "target_below"):
                val = float(val) if val else None
            setattr(item, key, val)
    item.save()
    return JsonResponse({"ok": True})


@login_required
def watchlist_refresh(request):
    items = Watchlist.objects.filter(user=request.user)
    payload = []
    for it in items:
        q = fetch_quote(it.symbol, it.exchange or "NS")
        if not q:
            continue
        it.last_price = q["price"]
        it.change_pct = q["change_pct"]
        it.display_name = q["name"] if q["name"] else it.display_name
        it.last_updated = timezone.now()
        it.save(update_fields=["last_price", "change_pct", "display_name", "last_updated"])
        payload.append({
            "id": it.id, "price": it.last_price, "change_pct": it.change_pct
        })
    return JsonResponse({"ok": True, "data": payload})


@login_required
def watchlist_spark(request, pk):
    item = get_object_or_404(Watchlist, pk=pk, user=request.user)
    series = fetch_sparkline(item.symbol, item.exchange or "NS")
    return JsonResponse({"ok": True, "series": series})


@login_required
def watchlist_import(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    symbols = request.POST.get("symbols", "")
    exchange = (request.POST.get("exchange") or "NS").upper()
    added = []
    for raw in [s.strip() for s in symbols.replace("\n", ",").split(",") if s.strip()]:
        if Watchlist.objects.filter(user=request.user, symbol=raw.upper(), exchange=exchange).exists():
            continue
        obj = Watchlist(user=request.user, symbol=raw.upper(), exchange=exchange)
        q = fetch_quote(obj.symbol, obj.exchange)
        if q:
            obj.last_price = q["price"]
            obj.change_pct = q["change_pct"]
            obj.display_name = q["name"]
            obj.last_updated = timezone.now()
        obj.save()
        added.append(obj.symbol)
    return JsonResponse({"ok": True, "added": added})


@login_required
def watchlist_export(request):
    rows = Watchlist.objects.filter(user=request.user).values_list(
        "symbol", "exchange", "group", "notes", "target_above", "target_below"
    )
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="watchlist.csv"'
    writer = csv.writer(resp)
    writer.writerow(["symbol", "exchange", "group", "notes", "target_above", "target_below"])
    for r in rows:
        writer.writerow(r)
    return resp