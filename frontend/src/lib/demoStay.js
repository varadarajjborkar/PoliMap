// A recorded stay, for looking at this screen without building one first.
//
// Reaching the real one takes a document read, a policy checked, a search run
// and a hospital chosen, which is a minute of waiting before every look at a
// change to the layout. This is one response from `GET /api/journey/{id}`,
// captured as it came, so what is laid out here is the shape the server
// actually sends rather than a guess at it.
//
// Development only. `import.meta.env.DEV` is replaced with `false` when the
// site is built, so the branch that reads this is dropped and the file goes
// with it.

export const demoStay = {
  "stage": "admitted",
  "stage_label": "In hospital",
  "stage_order": 1,
  "hospital_name": "Jayanagar Government Hospital",
  "room": "Single private room",
  "room_category": "single_private",
  "room_rate": 1430.0,
  "days_elapsed": 2,
  "pre_auth_filed": false,
  "accrued": 144750.0,
  "accrued_display": "₹1,44,750",
  "stages": [
    {
      "value": "pre_admission",
      "label": "Before admission",
      "order": 0,
      "kind": "back",
      "skips": []
    },
    {
      "value": "admitted",
      "label": "In hospital",
      "order": 1,
      "kind": "current",
      "skips": []
    },
    {
      "value": "discharge_planning",
      "label": "Going home",
      "order": 2,
      "kind": "advance",
      "skips": []
    },
    {
      "value": "settled",
      "label": "Claim settled",
      "order": 3,
      "kind": "skip",
      "skips": [
        "Going home"
      ]
    }
  ],
  "next_stage": "discharge_planning",
  "checklist": {
    "done": 0,
    "total": 8,
    "items": [
      {
        "id": "chase_preauth",
        "key": "chase_preauth",
        "values": {},
        "text": "Chase the pre-authorisation at the insurance desk, by name",
        "why": "An unread request is the commonest reason cashless turns into cash. Ask how much was approved, not only whether: insurers often approve less, and the gap is yours.",
        "urgent": true,
        "done": false
      },
      {
        "id": "check_room_rate",
        "key": "check_room_rate",
        "values": {},
        "text": "Check the room rate on the admission form",
        "why": "This one number decides how much of the rest of the bill is paid. Fix it now; nobody checks it at discharge.",
        "urgent": true,
        "done": false
      },
      {
        "id": "room_within_cap",
        "key": "room_within_cap",
        "values": {
          "cap": "₹5,000",
          "rate": "₹1,430"
        },
        "text": "Check your room bills at ₹5,000 a day or less",
        "why": "You were admitted at ₹1,430. Moving is easy on day one and hard on the last.",
        "urgent": true,
        "done": false
      },
      {
        "id": "daily_bill",
        "key": "daily_bill",
        "values": {},
        "text": "Ask for the bill every day, and read it",
        "why": "A charge questioned the same day gets corrected. At discharge it gets defended.",
        "urgent": true,
        "done": false
      },
      {
        "id": "keep_receipts",
        "key": "keep_receipts",
        "values": {},
        "text": "Keep every receipt, pharmacy ones too",
        "why": "Nothing is repaid without the original bill.",
        "urgent": false,
        "done": false
      },
      {
        "id": "ask_cost_first",
        "key": "ask_cost_first",
        "values": {},
        "text": "Ask what each test or scan costs before agreeing",
        "why": "Tests are where a bill grows fastest and a limit is crossed without anyone saying so.",
        "urgent": false,
        "done": false
      },
      {
        "id": "watch_the_room",
        "key": "watch_the_room",
        "values": {},
        "text": "Ask before any move to another room or to ICU",
        "why": "A new room means a new daily rate, and a new share on everything priced by room.",
        "urgent": false,
        "done": false
      },
      {
        "id": "consumables_running",
        "key": "consumables_running",
        "values": {},
        "text": "Ask the ward to itemise the consumables",
        "why": "You are paying for these, so a list is the only way to check them at discharge.",
        "urgent": false,
        "done": false
      }
    ]
  },
  "bill": null,
  "burn_down": {
    "sum_insured": 500000.0,
    "consumed": 144750.0,
    "remaining": 355250.0,
    "remaining_display": "₹3,55,250",
    "projected": 182500.0,
    "consumed_fraction": 0.2895,
    "will_exceed": false,
    "daily_run_rate": 18875.0,
    "daily_run_rate_display": "₹18,875",
    "days_of_cover_left": 18
  },
  "position": {
    "billed": 144750.0,
    "billed_display": "₹1,44,750",
    "insurer_pays": 98625.0,
    "insurer_pays_display": "₹98,625",
    "you_pay": 46125.0,
    "you_pay_display": "₹46,125",
    "steps": [
      {
        "label": "Room above your cover",
        "kind": "room_rent_cap",
        "key": "room_rent_cap",
        "values": {
          "rate": "₹8,000",
          "cap": "₹5,000"
        },
        "deducted": 6000.0,
        "deducted_display": "₹6,000",
        "explanation": "Your room is ₹8,000 a day and you are covered for ₹5,000. You pay the gap."
      },
      {
        "label": "Proportionate deduction",
        "kind": "proportionate",
        "key": "proportionate",
        "values": {
          "pct": "62.5%"
        },
        "deducted": 40125.0,
        "deducted_display": "₹40,125",
        "explanation": "Your room is above your category, so only 62.5% is paid on charges priced by room: surgeon, theatre and nursing. ICU, medicines, tests and implants are untouched."
      }
    ],
    "warnings": [
      {
        "key": "warn.proportionate",
        "text": "This room also costs about ₹40,125 in proportionate cuts, on top of the room gap.",
        "values": {
          "amount": "₹40,125"
        }
      }
    ]
  },
  "alerts": [
    {
      "kind": "room_over_limit",
      "key": "room_over_limit_knock_on",
      "values": {
        "rate": "₹8,000",
        "cap": "₹5,000",
        "days": "2",
        "excess": "₹6,000",
        "knock_on": "₹40,125"
      },
      "severity": "urgent",
      "title": "Your room costs more than your cover",
      "message": "Your room is ₹8,000 a day and you are covered for ₹5,000. After 2 days that is ₹6,000 in room rent, plus about ₹40,125 off your surgeon, theatre and nursing. That second cut lands on charges that are not the room, and it is the part most people never see coming.",
      "action": "Ask the insurance desk about a room within your limit. It stops further cuts from tomorrow.",
      "amount": 46125.0,
      "amount_display": "₹46,125"
    },
    {
      "kind": "pre_auth_due",
      "key": "pre_auth_due",
      "values": {},
      "severity": "urgent",
      "title": "Pre-authorisation needs filing",
      "message": "Cashless needs your insurer's approval before the procedure. Without it you pay the hospital and claim it back later.",
      "action": "Ask the insurance desk to file it now.",
      "amount": null,
      "amount_display": ""
    },
    {
      "kind": "room_over_limit",
      "key": "room_rate_conflict",
      "values": {
        "booked": "₹1,430",
        "observed": "₹8,000"
      },
      "severity": "attention",
      "title": "Your room is billing at a different rate",
      "message": "This stay was set up at ₹1,430 a day, and the charges recorded work out at ₹8,000. Both cannot be right.",
      "action": "If you moved room, this is expected. If not, ask the billing desk which rate applies.",
      "amount": null,
      "amount_display": ""
    }
  ],
  "timeline": [
    {
      "id": "a25f7674f8",
      "at": "2026-08-25T16:58:46.176072+00:00",
      "stage": "pre_admission",
      "title": "Planning your care",
      "title_key": "start",
      "description": "₹5,00,000 of cover. Looking at Jayanagar Government Hospital.",
      "note_key": "start_hospital",
      "values": {
        "cover": "₹5,00,000",
        "hospital": "Jayanagar Government Hospital"
      },
      "alert_count": 0,
      "kind": "advance",
      "skipped": [],
      "reason": ""
    },
    {
      "id": "496a77de6e",
      "at": "2026-08-25T16:58:46.180594+00:00",
      "stage": "admitted",
      "title": "In hospital",
      "title_key": "",
      "description": "Admitted to Single private room at ₹1,430 a day.",
      "note_key": "admitted_rate",
      "values": {
        "stage": "In hospital",
        "room": "Single private room",
        "room_key": "single_private",
        "rate": "₹1,430"
      },
      "alert_count": 1,
      "kind": "advance",
      "skipped": [],
      "reason": ""
    }
  ],
  "costs": [
    {
      "id": "abc2dc4d88",
      "head": "Room rent",
      "head_value": "room_rent",
      "amount": 8000.0,
      "amount_display": "₹8,000",
      "description": "Single private room, day 1",
      "at": "2026-08-25T16:58:46.184498+00:00",
      "receipt_name": ""
    },
    {
      "id": "bd81860d24",
      "head": "Tests and scans",
      "head_value": "investigations",
      "amount": 12400.0,
      "amount_display": "₹12,400",
      "description": "Angiogram and blood work",
      "at": "2026-08-25T16:58:46.188158+00:00",
      "receipt_name": ""
    },
    {
      "id": "c84cc03bc0",
      "head": "Surgeon's fee",
      "head_value": "surgeon_fee",
      "amount": 65000.0,
      "amount_display": "₹65,000",
      "description": "",
      "at": "2026-08-25T16:58:46.191935+00:00",
      "receipt_name": ""
    },
    {
      "id": "7d47445eb5",
      "head": "Operation theatre",
      "head_value": "ot_charges",
      "amount": 42000.0,
      "amount_display": "₹42,000",
      "description": "",
      "at": "2026-08-25T16:58:46.195778+00:00",
      "receipt_name": ""
    },
    {
      "id": "2ac595a00c",
      "head": "Medicines",
      "head_value": "pharmacy",
      "amount": 9350.0,
      "amount_display": "₹9,350",
      "description": "",
      "at": "2026-08-25T16:58:46.199603+00:00",
      "receipt_name": ""
    },
    {
      "id": "be5b1232a7",
      "head": "Room rent",
      "head_value": "room_rent",
      "amount": 8000.0,
      "amount_display": "₹8,000",
      "description": "Single private room, day 3",
      "at": "2026-08-25T16:58:46.203568+00:00",
      "receipt_name": ""
    }
  ]
}