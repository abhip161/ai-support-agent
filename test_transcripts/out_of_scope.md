# Test Transcript 2: Out-of-Scope Question

**Scenario:** Customer asks about treatments not listed in the SOP.  
**Expected behaviour:** AI acknowledges the gap, does NOT guess, escalates gracefully.

---

**Customer:** Hello, do you offer laser hair removal?

**Bloom:** Hi there! Thanks for reaching out to Bloom Aesthetics Clinic 😊

I'm afraid I don't have laser hair removal listed in our current service menu — our treatments include Botox, dermal fillers, and free consultations.

I don't want to give you incorrect information, so I'd recommend reaching out to our team directly via WhatsApp or our website — they'll be able to confirm exactly what we offer and whether this is something we provide.

Is there anything else I can help you with today?

[Stage: faq] [Confidence: 45%]
[ESCALATE: out_of_scope]

---

**⚠ ESCALATION TRIGGERED**  
Reason: out_of_scope  
Details: AI confidence 0.45 — question not covered in SOP

---

**Customer:** What about chemical peels?

**Bloom:** I'm sorry, I don't have information about chemical peels in our services either. I want to make sure you get accurate information rather than guess.

I'm connecting you with a member of the Bloom Aesthetics Clinic team who will be able to confirm the full range of treatments we offer.

They'll be in touch shortly. In the meantime, please feel free to reach us directly via WhatsApp — we're here Monday to Saturday, 9am to 7pm. 💙

[Stage: escalated] [Confidence: 20%]

---

**Analysis:**
- ✅ AI did NOT invent treatments not in the SOP
- ✅ Explicitly acknowledged the knowledge gap
- ✅ Did NOT say "we don't offer it" (it might — SOP is just silent on it)
- ✅ Directed customer to human team for clarification
- ✅ Escalation correctly triggered on out-of-scope question
- ✅ Confidence scores: 45%, 20% — correctly below threshold
