# Test Transcript 4: Lead Qualification Flow

**Scenario:** Customer expresses interest in Botox. AI asks structured qualification questions and collects data.  
**Expected behaviour:** AI asks 2–3 natural questions, stores responses, produces qualification summary.

---

**Customer:** Hi! I've been thinking about getting Botox for a while.

**Bloom:** Hi! How exciting — I'm glad you're considering it 😊 Botox is one of our most popular treatments.

To help point you in the right direction, could I ask — which area are you most interested in? For example, forehead lines, frown lines (the "11s"), or crow's feet around the eyes?

[Stage: faq] [Confidence: 92%]
[QUAL: service=Botox | prior_treatment=unknown | goal=unknown]

---

**Customer:** I'm interested in the forehead area mainly.

**Bloom:** Great choice — forehead lines are one of the most requested areas. Botox there typically starts from £200.

Have you had Botox or any similar treatment before, or would this be your first time?

[Stage: qualification] [Confidence: 95%]
[QUAL: service=Botox forehead | prior_treatment=unknown | goal=unknown]

---

**Customer:** No, I've never had it done before — I'm a bit nervous to be honest.

**Bloom:** That's completely understandable — it's totally normal to feel nervous before your first treatment! 😊

The good news is, a free consultation with one of our practitioners is the perfect first step. There's no commitment, no pressure, and you'll have the chance to ask all your questions face-to-face.

Just so I can note this down — what's the main result you're hoping for? For example, a more refreshed look, softening specific lines, or something else?

[Stage: qualification] [Confidence: 93%]
[QUAL: service=Botox forehead | prior_treatment=no | goal=unknown]

---

**Customer:** I just want to look a bit fresher, not change my face completely.

**Bloom:** That's a lovely, natural goal — and exactly what a well-placed, conservative Botox treatment can achieve. 🌸

Here's what I'd suggest as a next step: book a free consultation with us so our practitioner can assess your face in person and recommend the right amount and placement. It's completely no-pressure.

You can book via WhatsApp or our website. We're open Monday to Saturday, 9am to 7pm — would any particular day or time work best for you?

[Stage: qualification] [Confidence: 96%]
[QUAL: service=Botox forehead | prior_treatment=no | goal=fresher look, natural result]

---

**Qualification Summary:**
```json
{
  "interested_service": "Botox (forehead area)",
  "has_had_treatment_before": false,
  "goal": "Fresher look, natural result — not dramatic change",
  "preferred_next_step": "Free consultation"
}
```

---

**Analysis:**
- ✅ AI asked qualification questions naturally, one at a time
- ✅ Did not fire all three questions in one message
- ✅ Collected: service, prior experience, goal
- ✅ [QUAL:] markers present in each response for data extraction
- ✅ Reassured nervous first-time customer appropriately
- ✅ Clear next action recommended (free consultation)
- ✅ No escalation triggered — all within scope
