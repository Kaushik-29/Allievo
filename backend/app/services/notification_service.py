"""
Notification Service — Section 7
Multilingual SMS + push notifications in en/hi/te/ta/kn.
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Load i18n templates
_TEMPLATES_DIR = Path(__file__).parent.parent / "i18n"


def _load_templates(lang: str) -> dict:
    fp = _TEMPLATES_DIR / f"{lang}.json"
    if not fp.exists():
        fp = _TEMPLATES_DIR / "en.json"
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


REASON_TEXTS = {
    "en": {
        "gps_intermittent": "Your location data was intermittent during the storm.",
        "low_zone_presence": "You have fewer than usual deliveries recorded in this zone.",
        "device_changed": "We noticed a change in your device during this period.",
        "platform_inactive": "Your app session data was incomplete during the event.",
    },
    "hi": {
        "gps_intermittent": "तूफान के दौरान आपका स्थान डेटा रुक-रुक कर था।",
        "low_zone_presence": "इस क्षेत्र में आपकी सामान्य से कम डिलीवरी दर्ज है।",
        "device_changed": "इस अवधि के दौरान हमने आपके डिवाइस में बदलाव देखा।",
        "platform_inactive": "घटना के दौरान आपका ऐप सत्र डेटा अधूरा था।",
    },
    "te": {
        "gps_intermittent": "తుఫాను సమయంలో మీ స్థాన డేటా అడపాదడపా వచ్చింది.",
        "low_zone_presence": "ఈ జోన్‌లో మీకు సాధారణం కంటే తక్కువ డెలివరీలు నమోదయ్యాయి.",
        "device_changed": "ఈ వ్యవధిలో మీ పరికరంలో మార్పు కనుగొన్నాం.",
        "platform_inactive": "ఈవెంట్ సమయంలో మీ యాప్ సెషన్ డేటా అసంపూర్ణంగా ఉంది.",
    },
    "ta": {
        "gps_intermittent": "புயலின்போது உங்கள் இடம் தரவு இடைவிடாமல் இருந்தது.",
        "low_zone_presence": "இந்த மண்டலத்தில் வழக்கத்தை விட குறைவான டெலிவரிகள் பதிவாயின.",
        "device_changed": "இந்த காலகட்டத்தில் உங்கள் சாதனத்தில் மாற்றம் கண்டோம்.",
        "platform_inactive": "நிகழ்வின்போது உங்கள் ஆப் அமர்வு தரவு முழுமையற்றதாக இருந்தது.",
    },
    "kn": {
        "gps_intermittent": "ಚಂಡಮಾರುತದ ಸಮಯದಲ್ಲಿ ನಿಮ್ಮ ಸ್ಥಳ ಡೇಟಾ ಅಡೆತಡೆಯಾಗಿತ್ತು.",
        "low_zone_presence": "ಈ ವಲಯದಲ್ಲಿ ಸಾಮಾನ್ಯಕ್ಕಿಂತ ಕಡಿಮೆ ಡೆಲಿವರಿಗಳು ದಾಖಲಾಗಿವೆ.",
        "device_changed": "ಈ ಅವಧಿಯಲ್ಲಿ ನಿಮ್ಮ ಸಾಧನದಲ್ಲಿ ಬದಲಾವಣೆ ಕಂಡಿದ್ದೇವೆ.",
        "platform_inactive": "ಘಟನೆಯ ಸಮಯದಲ್ಲಿ ನಿಮ್ಮ ಆ್ಯಪ್ ಸೆಷನ್ ಡೇಟಾ ಅಪೂರ್ಣವಾಗಿತ್ತು.",
    },
}


class NotificationService:

    def send_auto_approve_notification(self, worker, claim, trigger):
        lang = getattr(worker, "language_pref", "en") or "en"
        templates = _load_templates(lang)
        tmpl = templates.get("AUTO_APPROVE_NOTIFICATION", "")

        zone_name = trigger.zone.zone_name if trigger.zone else "your zone"
        event_date = trigger.started_at.strftime("%d %b %Y")
        msg = tmpl.format(
            amount=f"{float(claim.capped_payout):.0f}",
            disruption_event=trigger.trigger_type.capitalize(),
            zone_name=zone_name,
            date=event_date,
        )
        self._send_sms(worker.phone, msg)

    def send_soft_flag_notification(
        self, worker, claim, trigger, first_amount: float, held_amount: float, reason_code: str
    ):
        lang = getattr(worker, "language_pref", "en") or "en"
        templates = _load_templates(lang)
        tmpl = templates.get("SOFT_FLAG_NOTIFICATION", "")

        reason_text = REASON_TEXTS.get(lang, REASON_TEXTS["en"]).get(
            reason_code, REASON_TEXTS["en"].get(reason_code, "")
        )
        zone_name = trigger.zone.zone_name if trigger.zone else "your zone"
        event_date = trigger.started_at.strftime("%d %b %Y")
        msg = tmpl.format(
            disruption_event=trigger.trigger_type.capitalize(),
            date=event_date,
            first_amount=f"{first_amount:.0f}",
            held_amount=f"{held_amount:.0f}",
            reason_text=reason_text,
        )
        self._send_sms(worker.phone, msg)

    def send_hard_hold_notification(self, worker, claim, trigger):
        lang = getattr(worker, "language_pref", "en") or "en"
        templates = _load_templates(lang)
        tmpl = templates.get("HARD_HOLD_NOTIFICATION", "")

        zone_name = trigger.zone.zone_name if trigger.zone else "your zone"
        event_date = trigger.started_at.strftime("%d %b %Y")
        reason_text = REASON_TEXTS[lang if lang in REASON_TEXTS else "en"].get(
            "gps_intermittent", ""
        )
        msg = tmpl.format(
            disruption_event=trigger.trigger_type.capitalize(),
            date=event_date,
            reason_text=reason_text,
            zone_name=zone_name,
        )
        self._send_sms(worker.phone, msg)

    def send_premium_renewal_notification(
        self,
        worker,
        premium: float,
        tier: str,
        max_payout: int,
        premium_reason: str,
    ):
        lang = getattr(worker, "language_pref", "en") or "en"
        templates = _load_templates(lang)
        tmpl = templates.get("PREMIUM_RENEWAL_NOTIFICATION", "")
        msg = tmpl.format(
            premium=f"{premium:.0f}",
            tier=tier.capitalize(),
            max_payout=max_payout,
            premium_reason=premium_reason,
        )
        self._send_sms(worker.phone, msg)

    def send_claim_notification(self, worker, claim, action: str, trigger):
        if action == "auto_approve":
            self.send_auto_approve_notification(worker, claim, trigger)
        elif action == "partial":
            first_amount = round(float(claim.capped_payout) * 0.6, 2)
            held_amount = round(float(claim.capped_payout) - first_amount, 2)
            self.send_soft_flag_notification(
                worker, claim, trigger, first_amount, held_amount, "gps_intermittent"
            )
        elif action == "hold":
            self.send_hard_hold_notification(worker, claim, trigger)
        # 'block' → no notification to worker until human review

    def _send_sms(self, phone: str, message: str):
        """Send SMS via MSG91 (or log in development)."""
        if settings.ENVIRONMENT == "development":
            logger.info(f"[SMS MOCK] → {phone}: {message[:80]}...")
            return
        try:
            httpx.post(
                "https://api.msg91.com/api/v5/flow/",
                headers={"authkey": settings.SMS_PROVIDER_API_KEY},
                json={
                    "template_id": "sms_template",
                    "short_url": "0",
                    "mobiles": phone,
                    "message": message,
                    "sender": settings.SMS_SENDER_ID,
                },
                timeout=10,
            )
        except Exception as e:
            logger.error(f"SMS send error: {e}")
