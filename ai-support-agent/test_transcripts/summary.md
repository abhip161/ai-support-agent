# Test Transcript 5: End-of-Session Conversation Summary

**Scenario:** A mixed conversation covering FAQ, qualification, and one out-of-scope question.  
**Expected behaviour:** AI handles conversation, then generates a clean structured summary.

---

**Customer:** Hey, what are your opening hours?

**Bloom:** Hi! 😊 We're open Monday to Saturday, 9am to 7pm. We're closed on Sundays.

Is there anything else I can help you with?

[Stage: faq] [Confidence: 99%]

---

**Customer:** Great. And how much is a consultation?

**Bloom:** Great news — consultations are completely free! ✨

They're a great way to meet our practitioners, discuss your goals, and find out which treatment is right for you — with no commitment required.

You can book via WhatsApp or through our website. Would you like to go ahead?

[Stage: faq] [Confidence: 99%]

---

**Customer:** I'm interested in fillers for my lips.

**Bloom:** Lovely choice! Lip fillers are one of our most popular treatments 💋

Dermal fillers start from £250 per syringe. For lips, the amount used can vary depending on your natural lip shape and the result you're going for — your free consultation will give you a fully personalised recommendation.

Have you had fillers before, or would this be your first time?

[Stage: qualification] [Confidence: 94%]
[QUAL: service=lip fillers | prior_treatment=unknown | goal=unknown]

---

**Customer:** Have you done lip fillers on people with thin lips?

**Bloom:** That's a really common question! I don't have specific case details to share, but our practitioners are experienced with a wide range of lip types and goals.

I'd highly recommend bringing this up in your free consultation — they'll be able to show you examples, discuss what's achievable for your lip shape, and set realistic expectations.

Would you like to book one? 😊

[Stage: qualification] [Confidence: 72%]
[QUAL: service=lip fillers | prior_treatment=unknown | goal=unknown]

---

**[Session ended by customer]**

---

## Generated Summary

```json
{
  "customer_intent": "Customer enquired about opening hours, consultation costs, and lip filler pricing. Expressed interest in booking lip filler treatment.",
  "sentiment": "positive",
  "key_details_collected": {
    "interested_service": "Lip fillers (dermal fillers)",
    "has_had_treatment_before": null,
    "goal": "Lip enhancement — concerned about suitability for thin lips"
  },
  "escalation_events": [],
  "sop_gaps": [
    "Turn 4: Customer asked about filler experience with thin lips — SOP has no case study or clinical detail data"
  ],
  "recommended_next_action": "Follow up with customer to book a free consultation. Share examples of lip filler results if available. Ensure practitioner notes thin lips concern.",
  "outcome": "qualified"
}
```

---

**Analysis:**
- ✅ Clean multi-topic conversation handled without errors
- ✅ Hours and consultation price answered directly from SOP
- ✅ Lip filler pricing cited correctly (from £250 per syringe)
- ✅ Out-of-scope question (case study / thin lips experience) handled gracefully — not invented
- ✅ SOP gap recorded for the thin lips question
- ✅ Qualification data partially collected (service = lip fillers)
- ✅ Summary JSON is clean, structured, and actionable
- ✅ Recommended next action is specific and useful for the human team
