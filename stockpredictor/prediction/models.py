from django.conf import settings
from django.db import models


class StockInfo(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    previous_close = models.FloatField(null=True, blank=True)
    current_price = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.full_name}"


class StockPrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock = models.ForeignKey(StockInfo, on_delete=models.CASCADE, null=True, blank=True)
    symbol = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    predicted_on = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField()
    trend = models.CharField(max_length=10)
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)

    def __str__(self):
        symbol = self.stock.symbol if self.stock else self.symbol
        return f"{symbol} ({self.trend}) - {self.user.username}"


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlist")
    symbol = models.CharField(max_length=20)
    exchange = models.CharField(max_length=10, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    last_price = models.FloatField(null=True, blank=True)
    change_pct = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    group = models.CharField(max_length=30, blank=True)
    pinned = models.BooleanField(default=False)
    notes = models.CharField(max_length=200, blank=True)
    target_above = models.FloatField(null=True, blank=True)
    target_below = models.FloatField(null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "symbol", "exchange")
        ordering = ("-pinned", "symbol")

    def __str__(self):
        ex = f".{self.exchange}" if self.exchange else ""
        return f"{self.user.username} - {self.symbol}{ex}"


class MLModelInfo(models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to='ml_models/')
    active = models.BooleanField(default=False)
    uploaded_on = models.DateTimeField(auto_now_add=True)


class PredictionLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    prediction_time = models.DateTimeField(auto_now_add=True)
    used_model = models.ForeignKey(MLModelInfo, on_delete=models.SET_NULL, null=True)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username