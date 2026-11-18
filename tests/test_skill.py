import os
import unittest
from unittest import mock

os.environ["ALEXA_VERIFY"] = "0"
from hub_printer import skill  # noqa: E402

IDLE = dict(state="standby", file="", elapsed=0, progress=0, hotend=25, hotend_target=0, bed=24, bed_target=0)
PRINTING = dict(IDLE, state="printing", elapsed=600, progress=0.25)


def ev(intent, sid="s1", **slots):
    return {"session": {"sessionId": sid},
            "request": {"type": "IntentRequest", "intent": {
                "name": intent, "slots": {k: {"value": str(v)} for k, v in slots.items()}}}}


class T(unittest.TestCase):
    def setUp(self):
        skill._pending.clear()

    @mock.patch("hub_printer.moonraker.gcode")
    @mock.patch("hub_printer.moonraker.status", return_value=IDLE)
    def test_preheat_needs_confirmation(self, _st, gc):
        r = skill.handle(ev("PrecalentarIntent", material="pla"))
        gc.assert_not_called()                       # nada se ejecuta aun
        self.assertFalse(r["response"]["shouldEndSession"])
        skill.handle(ev("AMAZON.YesIntent"))
        gc.assert_called_once_with("M104 S210\nM140 S60")

    @mock.patch("hub_printer.moonraker.gcode")
    @mock.patch("hub_printer.moonraker.status", return_value=IDLE)
    def test_no_cancels_and_other_intent_discards(self, _st, gc):
        skill.handle(ev("PrecalentarIntent", material="pla"))
        skill.handle(ev("AMAZON.NoIntent"))
        skill.handle(ev("AMAZON.YesIntent"))
        skill.handle(ev("PrecalentarIntent", material="pla"))
        skill.handle(ev("EstadoIntent"))             # cambia de tema: descarta
        skill.handle(ev("AMAZON.YesIntent"))
        gc.assert_not_called()

    @mock.patch("hub_printer.moonraker.gcode")
    @mock.patch("hub_printer.moonraker.status", return_value=IDLE)
    def test_yes_without_pending_and_other_session(self, _st, gc):
        skill.handle(ev("PrecalentarIntent", sid="a", material="pla"))
        skill.handle(ev("AMAZON.YesIntent", sid="b"))
        gc.assert_not_called()

    @mock.patch("hub_printer.moonraker.gcode")
    @mock.patch("hub_printer.moonraker.status", return_value=IDLE)
    def test_expired(self, _st, gc):
        skill.handle(ev("PrecalentarIntent", material="pla"))
        with mock.patch("time.time", return_value=9e12):
            skill.handle(ev("AMAZON.YesIntent"))
        gc.assert_not_called()

    @mock.patch("hub_printer.moonraker.gcode")
    @mock.patch("hub_printer.moonraker.status", return_value=IDLE)
    def test_limits(self, _st, gc):
        r = skill.handle(ev("PrecalentarIntent", hotend=400))
        self.assertIn("no puede pasar", r["response"]["outputSpeech"]["text"])
        self.assertEqual(skill._pending, {})

    @mock.patch("hub_printer.moonraker.status", return_value=PRINTING)
    def test_refuse_preheat_while_printing_and_status(self, _st):
        r = skill.handle(ev("PrecalentarIntent", material="pla"))
        self.assertEqual(skill._pending, {})
        self.assertIn("en curso", r["response"]["outputSpeech"]["text"])
        r = skill.handle(ev("EstadoIntent"))
        self.assertIn("25 por ciento", r["response"]["outputSpeech"]["text"])

    @mock.patch("hub_printer.moonraker.cancel")
    @mock.patch("hub_printer.moonraker.status", return_value=PRINTING)
    def test_cancel_needs_confirmation(self, _st, c):
        skill.handle(ev("CancelarImpresionIntent"))
        c.assert_not_called()
        skill.handle(ev("AMAZON.YesIntent"))
        c.assert_called_once()


if __name__ == "__main__":
    unittest.main()
