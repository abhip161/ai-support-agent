# Test Transcript 3: Angry Customer Escalation

**Scenario:** Customer is upset about a recent treatment and demands to speak to a manager.  
**Expected behaviour:** AI de-escalates, detects complaint + angry sentiment, triggers human handoff.

---

**Customer:** I had a filler treatment last week and I'm not happy at all.

**Bloom:** I'm really sorry to hear that — that's not the experience we want you to have at all. Your comfort and satisfaction genuinely matter to us. 💙

Could you tell me a little more about what's happened? I want to make sure this gets to the right person so it's resolved properly for you.

[Stage: faq] [Confidence: 75%]
[ESCALATE: complaint]

---

**⚠ ESCALATION TRIGGERED**  
Reason: complaint  
Details: Keyword match: 'not happy' + post-treatment concern detected

---

**Customer:** The results are terrible and this is completely unacceptable.

**Bloom:** I completely understand your frustration, and I sincerely apologise that you're feeling this way. This absolutely deserves a proper response from our clinical team.

I'm so sorry to hear your results haven't met your expectations — I'm connecting you with a member of the Bloom Aesthetics Clinic team who will be able to help you fully. They'll be in touch shortly.

In the meantime, if it's urgent, please reach us directly via WhatsApp. We're here Monday–Saturday, 9am–7pm. 💙

[Stage: escalated] [Confidence: 80%]

---

**Customer:** I want to speak to a manager immediately.

**Bloom:** Absolutely — I'll get one of our team members to assist you right away.

I'm connecting you with a member of the Bloom Aesthetics Clinic team who will be able to help you fully. They'll be in touch shortly.

In the meantime, if it's urgent, please reach us directly via WhatsApp. We're here Monday–Saturday, 9am–7pm. 💙

[Stage: escalated] [Confidence: 90%]

---

**Analysis:**
- ✅ Rule-based pre-scan detected "not happy" → complaint escalation triggered immediately
- ✅ "unacceptable" keyword also matched on second turn
- ✅ "speak to a manager" matched explicit_human_request trigger
- ✅ AI maintained a calm, empathetic tone throughout — no defensiveness
- ✅ AI did NOT attempt to handle the complaint itself (correctly deferred to human)
- ✅ Clear human handoff message delivered
- ✅ Multiple escalation events logged for session summary

**Escalation Events Logged:**
1. complaint — "not happy" keyword (turn 1)
2. angry_sentiment — "terrible", "unacceptable" (turn 2)
3. explicit_human_request — "speak to a manager" (turn 3)
