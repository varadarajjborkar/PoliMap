// Kannada (ಕನ್ನಡ). The interface's own words, keyed to the English
// that the call site passes alongside them.
//
// Its own module so that a reader downloads one language rather than five.
// lib/i18n.js imports this on demand, when somebody asks for it, and never
// otherwise. A key here with no call site, or a call site with no key here,
// fails scripts/check-strings.mjs.

export default {
  'nav.start_over': 'ಮತ್ತೆ ಶುರು ಮಾಡಿ',
  'nav.setup': 'ಸಿದ್ಧತೆ',
  'nav.stay': 'ಆಸ್ಪತ್ರೆಯಲ್ಲಿ',
  'nav.back.hospitals': 'ಆಸ್ಪತ್ರೆಗಳಿಗೆ ಹಿಂತಿರುಗಿ',

  'signin.title': 'ನಿಮ್ಮ ಆಸ್ಪತ್ರೆ ಚಿಕಿತ್ಸೆಗೆ ಎಷ್ಟು ಖರ್ಚಾಗುತ್ತದೆ ಎಂದು ತಿಳಿಯಿರಿ',
  'signin.subtitle':
    'ನಿಮ್ಮ ಚಿಕಿತ್ಸೆಗಳನ್ನು ಉಳಿಸಿಕೊಳ್ಳಲು ಒಂದು ಹೆಸರು ಆಯ್ಕೆ ಮಾಡಿ. ಅದು ಈ ಸಾಧನದಲ್ಲೇ ಉಳಿಯುತ್ತದೆ.',
  'signin.name': 'ನಿಮ್ಮನ್ನು ಏನೆಂದು ಕರೆಯಬೇಕು?',
  'signin.continue': 'ಮುಂದುವರಿಯಿರಿ',
  'signin.no_account':
    'ಪಾಸ್‌ವರ್ಡ್ ಇಲ್ಲ, ಖಾತೆ ಇಲ್ಲ. ನಿಮ್ಮ ಗುರುತು ತಿಳಿಸುವ ಯಾವ ಮಾಹಿತಿಯೂ ಎಲ್ಲಿಗೂ ಕಳುಹಿಸುವುದಿಲ್ಲ, ಮತ್ತು ಈ ಸಾಧನದಲ್ಲಿ ಬೇರೆ ಹೆಸರು ಹಾಕಿದರೆ ಬೇರೆಯದೇ, ಪ್ರತ್ಯೇಕ ಚಿಕಿತ್ಸೆಗಳು ತೆರೆಯುತ್ತವೆ.',
  'home.title': 'ನಿಮ್ಮ ಚಿಕಿತ್ಸೆಗಳು',
  'home.new': 'ಹೊಸ ಚಿಕಿತ್ಸೆ ಶುರು ಮಾಡಿ',

  'step.upload': 'ನಿಮ್ಮ ಪಾಲಿಸಿ',
  'step.policy': 'ನಿಮ್ಮ ಕವರೇಜ್',
  'step.search': 'ಆಸ್ಪತ್ರೆಗಳು',
  'step.short.upload': 'ಪಾಲಿಸಿ',
  'step.short.policy': 'ಕವರೇಜ್',
  'step.short.search': 'ಆಸ್ಪತ್ರೆಗಳು',

  'results.you_pay': 'ನೀವು ಪಾವತಿಸುವುದು',
  'results.insurer_pays': 'ವಿಮಾ ಕಂಪನಿ ಪಾವತಿಸುವುದು',

  'journey.stage.pre_admission': 'ದಾಖಲಾಗುವ ಮೊದಲು',
  'journey.stage.admitted': 'ಆಸ್ಪತ್ರೆಯಲ್ಲಿ',
  'journey.stage.discharge_planning': 'ಮನೆಗೆ ಹೋಗುವ ಸಿದ್ಧತೆ',
  'journey.stage.settled': 'ಕ್ಲೇಮ್ ಇತ್ಯರ್ಥವಾಗಿದೆ',
  'journey.download': 'ಈ ಪೂರ್ಣ ವಿವರ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ',
  'journey.download.why':
    'ನಿಮ್ಮ ಕವರೇಜ್, ಅಂದಾಜು, ಇಲ್ಲಿಯವರೆಗಿನ ಬಿಲ್, ಮತ್ತು ಇನ್ನೂ ಮಾಡಬೇಕಾದದ್ದು. ವಿಮಾ ಕೌಂಟರ್‌ಗೆ ಒಯ್ಯಲು ಒಂದೇ ಪುಟ.',
  'journey.charges': 'ಇಲ್ಲಿಯವರೆಗಿನ ಖರ್ಚು',
  'journey.add_charge': 'ಖರ್ಚು ಸೇರಿಸಿ',
  'journey.timeline': 'ಇಲ್ಲಿಯವರೆಗೆ ಏನಾಯಿತು',
  'journey.checklist': 'ಈಗ ಏನು ಮಾಡಬೇಕು',

  'bill.title': 'ಕೊನೆಯ ಬಿಲ್ ಪರಿಶೀಲಿಸಿ',
  'bill.subtitle':
    'ಯಾವ ಪಾಲಿಸಿಯೂ ಪಾವತಿಸದ ವಸ್ತುಗಳ IRDAI ಪಟ್ಟಿಯ ವಿರುದ್ಧ, ಮತ್ತು ನಿಮ್ಮ ಸ್ವಂತ ಕವರೇಜ್ ವಿರುದ್ಧ.',
  'bill.upload': 'ಬಿಲ್ ಫೋಟೋ ತೆಗೆಯಿರಿ ಅಥವಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
  'bill.reading': 'ಬಿಲ್ ಓದಲಾಗುತ್ತಿದೆ…',
  'bill.nothing': 'IRDAI ಪಟ್ಟಿ ಅಥವಾ ನಿಮ್ಮ ಪಾಲಿಸಿಯ ವಿರುದ್ಧ ಈ ಬಿಲ್‌ನಲ್ಲಿ ಏನೂ ಎದ್ದು ಕಾಣಲಿಲ್ಲ.',
  'bill.settles_to': 'ಈ ಬಿಲ್‌ನ ಲೆಕ್ಕ',
  'bill.show_lines': 'ಓದಿದ ಸಾಲುಗಳನ್ನು ತೋರಿಸಿ',
  'bill.hide_lines': 'ಸಾಲುಗಳನ್ನು ಮರೆಮಾಡಿ',
  'bill.another': 'ಬೇರೆ ಬಿಲ್ ಪರಿಶೀಲಿಸಿ',
  'bill.to_ask': 'ಕೇಳಬೇಕಾದದ್ದು',
  'bill.nothing_to_raise': 'ಎತ್ತಬೇಕಾದದ್ದು ಏನೂ ಇಲ್ಲ',

  'help.open': 'ಸಹಾಯ',
  'help.title': 'ಸಹಾಯ',
  'help.close': 'ಸಹಾಯ ಮುಚ್ಚಿ',
  'help.new_chat': 'ಹೊಸ ಸಂಭಾಷಣೆ',
  'help.recentre': 'ಮಧ್ಯಕ್ಕೆ ತನ್ನಿ',
  'help.thinking': 'ನೋಡುತ್ತಿದ್ದೇವೆ',
  'help.placeholder': 'ಈ ಪರದೆಯ ಬಗ್ಗೆ ಏನು ಬೇಕಾದರೂ ಕೇಳಿ',
  'help.send': 'ಕೇಳಿ',
  'help.raise': 'ಇದನ್ನು ತಂಡಕ್ಕೆ ತಲುಪಿಸಿ',
  'help.ticket_title': 'ತಂಡಕ್ಕೆ ತಲುಪಿಸಿ',
  'help.ticket_subject': 'ಒಂದೇ ಸಾಲಿನಲ್ಲಿ',
  'help.ticket_detail': 'ಇನ್ನೇನಾದರೂ ಹೇಳಬೇಕಿದ್ದರೆ',
  'help.file': 'ಕಳುಹಿಸಿ',
  'help.filing': 'ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ',
  'help.cancel': 'ಬೇಡ',
  'help.footer':
    'ಇದು ಕೇವಲ ಮಾರ್ಗದರ್ಶನ, ವೈದ್ಯಕೀಯ ಸಲಹೆ ಅಲ್ಲ, ಮತ್ತು ಇದು ನಿಮ್ಮ ಚಿಕಿತ್ಸೆಯಲ್ಲಿ ಏನನ್ನೂ ಬದಲಾಯಿಸಲಾರದು. ಮುಚ್ಚಿದ ಕೂಡಲೇ ಇಲ್ಲಿನ ಸಂಭಾಷಣೆ ಅಳಿಸಿಹೋಗುತ್ತದೆ.',
  'settings.tickets': 'ನಿಮ್ಮ ಟಿಕೆಟ್‌ಗಳು',
  'settings.tickets.none':
    'ಇನ್ನೂ ಏನೂ ಕಳುಹಿಸಿಲ್ಲ. ಸಹಾಯ ಕಿಟಕಿಯಿಂದ ನೀವು ಕಳುಹಿಸಿದ್ದು ಇಲ್ಲಿ ಅದರ ಸಂಖ್ಯೆಯೊಂದಿಗೆ ಕಾಣಿಸುತ್ತದೆ.',
  'settings.tickets.stage': 'ಸ್ವೀಕರಿಸಲಾಗಿದೆ',
  'settings.tickets.note':
    'ಇದರ ಮೇಲೆ ಇನ್ನೂ ಯಾವ ಕೆಲಸವೂ ಶುರುವಾಗಿಲ್ಲ, ಮತ್ತು ಸುಳ್ಳು ತೋರಿಕೆಯ ಸ್ಥಿತಿಗಿಂತ ಇದನ್ನು ಹೇಳುವುದೇ ಒಳ್ಳೆಯದು',
  'settings.language': 'ಭಾಷೆ',
  'settings.language.hint':
    'ಇದು ಆ್ಯಪ್‌ನ ಸ್ವಂತ ಭಾಷೆಯನ್ನು ಬದಲಾಯಿಸುತ್ತದೆ. ನಿಮ್ಮ ಪಾಲಿಸಿಯಿಂದ ಓದಿದ ವಿಷಯ ದಾಖಲೆಯ ಭಾಷೆಯಲ್ಲೇ ಉಳಿಯುತ್ತದೆ.',
  'settings.theme': 'ನೋಟ',
  'settings.text_size': 'ಅಕ್ಷರದ ಗಾತ್ರ',

  'nav.home': 'ನಿಮ್ಮ ಚಿಕಿತ್ಸೆಗಳು',
  'nav.steps': '{count} ಹಂತಗಳು',
  'nav.text.normal': 'ಸಾಮಾನ್ಯ ಅಕ್ಷರ ಗಾತ್ರಕ್ಕೆ ತನ್ನಿ',
  'nav.text.larger': 'ಅಕ್ಷರಗಳನ್ನು ದೊಡ್ಡದು ಮಾಡಿ',
  'nav.settings': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
  'nav.sections': 'ವಿಭಾಗಗಳು',

  'signin.placeholder': 'ನಿಮ್ಮ ಹೆಸರು, ಅಥವಾ ನಿಮಗೆ ನೆನಪಿರುವ ಯಾವುದಾದರೂ',

  'home.resume': 'ಬಿಟ್ಟಲ್ಲಿಂದಲೇ ಮುಂದುವರಿಸಿ, ಅಥವಾ ಹೊಸ ದಾಖಲಾತಿ ಶುರು ಮಾಡಿ.',
  'home.first': 'ಪಾಲಿಸಿ ಓದಿಸುವುದರಿಂದ ಶುರು ಮಾಡಿ. ಆ ನಂತರದ್ದೆಲ್ಲ ಇಲ್ಲೇ ಉಳಿಯುತ್ತದೆ.',
  'home.switch_user': 'ನೀವಲ್ಲವೇ?',
  'home.policy_read': 'ಪಾಲಿಸಿ ಓದಲಾಗಿದೆ',
  'home.delete': '{stay} ಅಳಿಸಿ',
  'home.delete.short': 'ಅಳಿಸಿ',
  'home.stored_locally':
    'ಇವು ಈ ಸಾಧನದಲ್ಲಿ ಮಾತ್ರ ಇರುತ್ತವೆ. ಬ್ರೌಸರ್ ಮಾಹಿತಿ ಅಳಿಸಿದರೆ ಇವು ಹೋಗುತ್ತವೆ.',

  'restore.opening':
    'ನಿಮ್ಮ ಚಿಕಿತ್ಸೆಯನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ. ಸರ್ವರ್ ಎಚ್ಚರಗೊಳ್ಳಲು ಸ್ವಲ್ಪ ಸಮಯ ಬೇಕಾಗಬಹುದು.',

  'reading.policy': 'ನಿಮ್ಮ ಪಾಲಿಸಿ ಓದಲಾಗುತ್ತಿದೆ',
  'reading.policy.waiting': 'ನಿಮ್ಮ ಕಡತಗಳನ್ನು ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ. ಈ ಪುಟವನ್ನು ತೆರೆದಿಡಿ.',
  'reading.policy.hint':
    'ಉದ್ದದ ದಾಖಲೆಗಳು ಮತ್ತು ಫೋನ್ ಫೋಟೋಗಳು ಹೆಚ್ಚು ಸಮಯ ತೆಗೆದುಕೊಳ್ಳುತ್ತವೆ. ಇದನ್ನು ಹಿನ್ನೆಲೆಯಲ್ಲಿ ತೆರೆದಿಡಬಹುದು.',
  'reading.search': 'ನಿಮ್ಮ ಆಯ್ಕೆಗಳನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ',
  'reading.search.hint':
    'ವ್ಯಾಪ್ತಿಯ ಪ್ರತಿ ಆಸ್ಪತ್ರೆಯ ಖರ್ಚನ್ನು ನಿಮ್ಮ ಪಾಲಿಸಿಯ ಪ್ರಕಾರ ಒಂದೊಂದಾಗಿ ಲೆಕ್ಕ ಹಾಕಲಾಗುತ್ತಿದೆ.',
  'reading.bill': 'ನಿಮ್ಮ ಬಿಲ್ ಓದಲಾಗುತ್ತಿದೆ',
  'reading.bill.waiting': 'ಬಿಲ್ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ. ಈ ಪುಟವನ್ನು ತೆರೆದಿಡಿ.',
  'reading.bill.hint':
    'ಫೋಟೋಗೆ PDF ಗಿಂತ ಹೆಚ್ಚು ಸಮಯ ಬೇಕು, ಏಕೆಂದರೆ ಪರಿಶೀಲಿಸುವ ಮೊದಲು ಪ್ರತಿ ಸಾಲನ್ನೂ ಗುರುತಿಸಬೇಕು.',

  'locked.policy': 'ನಿಮ್ಮ ಕವರ್',
  'locked.policy.why':
    'ಪಾಲಿಸಿ ಓದಿದ ನಂತರ, ನಿಮಗೆ ಯಾವುದಕ್ಕೆಲ್ಲ ಕವರ್ ಇದೆ ಎಂಬುದೆಲ್ಲ ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತದೆ, ಮತ್ತು ನಾವು ತಪ್ಪಾಗಿ ಓದಿದ್ದನ್ನು ನೀವು ಸರಿಪಡಿಸಬಹುದು.',
  'locked.search': 'ಆಸ್ಪತ್ರೆಗಳು',
  'locked.search.why':
    'ನಾವು ವ್ಯಾಪ್ತಿಯ ಪ್ರತಿ ಆಸ್ಪತ್ರೆಯ ಖರ್ಚನ್ನು ನಿಮ್ಮದೇ ಪಾಲಿಸಿಯ ಪ್ರಕಾರ ಲೆಕ್ಕ ಹಾಕುತ್ತೇವೆ, ಆದ್ದರಿಂದ ಮೊದಲು ನಿಮ್ಮ ಕವರ್ ಬೇಕು.',

  'gone.title': 'ಈ ಚಿಕಿತ್ಸೆ ಈ ಸಾಧನದಲ್ಲಿ ಇಲ್ಲ',
  'gone.why':
    'ಚಿಕಿತ್ಸೆಗಳು ಅವು ಶುರುವಾದ ಸಾಧನದಲ್ಲೇ ಉಳಿಯುತ್ತವೆ. ಈ ಕೊಂಡಿ ಬೇರೊಂದು ಫೋನ್ ಅಥವಾ ಬೇರೊಂದು ಬ್ರೌಸರ್‌ನಿಂದ ಬಂದಿದ್ದರೆ, ಆ ದಾಖಲಾತಿ ಅಲ್ಲೇ ಇದೆ, ಇಲ್ಲಿ ಅಲ್ಲ.',
  'gone.home': 'ನಿಮ್ಮ ಚಿಕಿತ್ಸೆಗಳು',
  'gone.new': 'ಹೊಸ ಚಿಕಿತ್ಸೆ ಶುರು ಮಾಡಿ',

  'rail.cover': 'ನಿಮ್ಮ ಕವರ್',
  'rail.check': 'ನಾವು ಓದಿದ್ದನ್ನು ನೋಡಿ',
  'rail.room': 'ಕವರ್ ಇರುವ ಕೊಠಡಿ',
  'rail.treatment': 'ಚಿಕಿತ್ಸೆ',
  'rail.cheapest': 'ನಿಮಗೆ ಅತ್ಯಂತ ಕಡಿಮೆ ಖರ್ಚಿನ',
  'rail.title': 'ಇಲ್ಲಿಯವರೆಗೆ',
  'rail.change': 'ಬದಲಾಯಿಸಿ',

  'activity.title': 'ಚಟುವಟಿಕೆ',
  'activity.subtitle': 'ವ್ಯವಸ್ಥೆ ತೆಗೆದುಕೊಳ್ಳುವ ಪ್ರತಿ ಹೆಜ್ಜೆ',
  'activity.live': 'ಚಾಲನೆಯಲ್ಲಿ',
  'activity.idle': 'ನಿಂತಿದೆ',
  'activity.empty': 'ಪಾಲಿಸಿ ಓದುತ್ತಿದ್ದಂತೆ ಇಲ್ಲಿ ಹೆಜ್ಜೆಗಳು ಕಾಣಿಸುತ್ತವೆ.',
  'activity.count': '{count} ಹಂತಗಳು',
  'activity.attention': '{count} ಗಮನ ಬೇಕು',

  'time.now': 'ಈಗಷ್ಟೇ',
  'time.minutes': '{count} ನಿಮಿಷಗಳ ಹಿಂದೆ',
  'time.hours': '{count} ಗಂಟೆಗಳ ಹಿಂದೆ',
  'time.yesterday': 'ನಿನ್ನೆ',
  'time.days': '{count} ದಿನಗಳ ಹಿಂದೆ',

  'error.dismiss': 'ಮುಚ್ಚಿ',

  'upload.title': 'ನಿಮ್ಮ ಆಸ್ಪತ್ರೆ ಚಿಕಿತ್ಸೆಗೆ ನಿಜವಾಗಿ ಎಷ್ಟು ಖರ್ಚಾಗುತ್ತದೆ ಎಂದು ತಿಳಿಯಿರಿ',
  'upload.subtitle':
    'ನಿಮ್ಮ ಆರೋಗ್ಯ ವಿಮಾ ಪಾಲಿಸಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ಯಾವ ಆಸ್ಪತ್ರೆಗಳಲ್ಲಿ ನಿಮಗೆ ಕವರ್ ಇದೆ, ಯಾವ ಕೊಠಡಿ ನಿಮ್ಮ ಹಕ್ಕು, ಮತ್ತು ನೀವೇ ಎಷ್ಟು ಕೊಡಬೇಕು ಎಂದು ನಾವು ಹೇಳುತ್ತೇವೆ.',
  'upload.tab.file': 'ನನ್ನ ಪಾಲಿಸಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
  'upload.tab.manual': 'ನನ್ನ ಬಳಿ ದಾಖಲೆ ಇಲ್ಲ',
  'upload.insurer': 'ನಿಮ್ಮ ವಿಮೆ ಯಾರ ಜೊತೆ?',
  'upload.insurer.hint':
    'ಇದರಿಂದ ಯಾವ ಆಸ್ಪತ್ರೆಗಳಲ್ಲಿ ನಿಮಗೆ ನಗದುರಹಿತ ಚಿಕಿತ್ಸೆ ಸಿಗುತ್ತದೆ ಎಂದು ನಮಗೆ ತಿಳಿಯುತ್ತದೆ.',
  'upload.insurer.choose': 'ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ಆರಿಸಿ',
  'upload.insurer.companies': 'ವಿಮಾ ಕಂಪನಿಗಳು',
  'upload.insurer.schemes': 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು',
  'upload.drop': 'ನಿಮ್ಮ ಪಾಲಿಸಿಯನ್ನು ಇಲ್ಲಿ ಬಿಡಿ, ಅಥವಾ ಆರಿಸಲು ಒತ್ತಿ',
  'upload.drop.more': 'ಇನ್ನಷ್ಟು ಪುಟ ಸೇರಿಸಿ, ಅಥವಾ ಆರಿಸಲು ಒತ್ತಿ',
  'upload.drop.hint':
    'PDF ಮತ್ತು ಫೋಟೋ, ಎರಡೂ ನಡೆಯುತ್ತವೆ, ಮತ್ತು ನೀವು ಹಲವು ಸೇರಿಸಬಹುದು. ಫೋನ್‌ನಲ್ಲಿ ತೆಗೆದ ಪ್ರತಿ ಪುಟದ ಫೋಟೋ ಕೂಡ ಸರಿ; ನಾವು ಅವನ್ನು ಓದಿ ಒಟ್ಟುಗೂಡಿಸುತ್ತೇವೆ.',
  'upload.too_many':
    'ಇದು {limit} ಕಡತಗಳಿಗಿಂತ ಹೆಚ್ಚು. ನಿಮ್ಮ ಕವರ್ ಬರೆದಿರುವ ಪುಟಗಳೇ ಸಾಮಾನ್ಯವಾಗಿ ಸಾಕು.',
  'upload.too_large':
    'ಇವು ಸೇರಿ {size} MB ಆಗುತ್ತವೆ, ನಾವು {limit} MB ವರೆಗೆ ಓದಬಲ್ಲೆವು. ನಿಮ್ಮ ಕವರ್ ಬರೆದಿರುವ ಪುಟಗಳೇ ಸಾಮಾನ್ಯವಾಗಿ ಸಾಕು.',
  'upload.remove': '{name} ತೆಗೆದುಹಾಕಿ',
  'upload.reading': 'ನಿಮ್ಮ ಪಾಲಿಸಿ ಓದಲಾಗುತ್ತಿದೆ.',
  'upload.read': 'ನನ್ನ ಪಾಲಿಸಿ ಓದಿ',
  'upload.read_many': 'ಈ {count} ದಾಖಲೆಗಳನ್ನು ಓದಿ',
  'upload.done': 'ನಿಮ್ಮ ಪಾಲಿಸಿ ಓದಲಾಗಿದೆ',
  'upload.done.hint':
    'ಅದರಲ್ಲಿ ಏನಿದೆ ಎಂಬುದು ಕೆಳಗಿದೆ. ಮುಂದೆ ಹೋಗುವ ಮೊದಲು ನಾವು ತಪ್ಪಾಗಿ ಓದಿದ್ದನ್ನು ಸರಿಪಡಿಸಿ.',

  'manual.sum_insured': 'ಒಟ್ಟು ಕವರ್ ಮೊತ್ತ',
  'manual.sum_insured.hint': 'ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ವರ್ಷಕ್ಕೆ ಗರಿಷ್ಠ ಎಷ್ಟು ಕೊಡುತ್ತದೆ.',
  'manual.room': 'ಕೊಠಡಿ ಬಾಡಿಗೆ ಮಿತಿ',
  'manual.room.hint':
    'ಬಹುತೇಕ ಪಾಲಿಸಿಗಳಲ್ಲಿ ಇದಕ್ಕೆ ಮಿತಿ ಇರುತ್ತದೆ. ಮಿತಿಗಿಂತ ಮೇಲಿನ ಕೊಠಡಿ ತೆಗೆದುಕೊಂಡರೆ ಉಳಿದ ಖರ್ಚುಗಳಲ್ಲೂ ವಿಮಾ ಕಂಪನಿ ಕಡಿಮೆ ಕೊಡುತ್ತದೆ.',
  'manual.room.flat': 'ದಿನಕ್ಕೆ ನಿಗದಿತ ಮೊತ್ತ',
  'manual.room.pct': 'ನನ್ನ ಕವರ್‌ನ ಶೇಕಡಾ',
  'manual.room.none': 'ಮಿತಿ ಇಲ್ಲ',
  'manual.room.amount': 'ದಿನದ ಮೊತ್ತ',
  'manual.room.percent': 'ಕವರ್‌ನ ಶೇಕಡಾ, ದಿನಕ್ಕೆ',
  'manual.copay': 'ನಿಮ್ಮ ಪಾಲು',
  'manual.copay.hint':
    'ಪ್ರತಿ ಕ್ಲೇಮ್‌ನ ಎಷ್ಟು ಪಾಲನ್ನು ನೀವೇ ಕೊಡುತ್ತೀರಿ. ಇಲ್ಲದಿದ್ದರೆ 0 ಬರೆಯಿರಿ.',
  'manual.working': 'ನಡೆಯುತ್ತಿದೆ…',
  'manual.continue': 'ಮುಂದುವರಿಯಿರಿ',

  'treatment.placeholder': 'ನಿಮಗೆ ಹೇಳಿದ್ದನ್ನು ಬರೆಯಿರಿ, ಉದಾ ಸ್ಟೆಂಟ್, ಹೆರಿಗೆ, ಪಿತ್ತಕೋಶ',
  'treatment.no_match':
    'ಇದಕ್ಕೆ ಏನೂ ಸಿಗಲಿಲ್ಲ. ಸುಲಭವಾದ ಪದ ಪ್ರಯತ್ನಿಸಿ, ಉದಾ ದೇಹದ ಆ ಭಾಗ, ಅಥವಾ ವೈದ್ಯರ ಚೀಟಿಯಲ್ಲಿ ಬರೆದ ಪದ.',

  'policy.warnings': 'ನೀವು ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ದಾಖಲೆಯ ಬಗ್ಗೆ',
  'policy.title': 'ನಿಮ್ಮ ಕವರ್',
  'policy.sum_insured': 'ಈ ವರ್ಷದ ಒಟ್ಟು ಕವರ್',
  'policy.sum_insured.hint': 'ನಿಮ್ಮ ಪಾಲಿಸಿಯಲ್ಲಿ ಬರೆದಂತೆ, ಉದಾ 5 ಲಕ್ಷ ಅಥವಾ 500000',
  'policy.remaining': 'ಈ ವರ್ಷ ಉಳಿದಿರುವ ಕವರ್',
  'policy.remaining.hint': 'ಈ ಪಾಲಿಸಿ ವರ್ಷದಲ್ಲಿ ಈಗಾಗಲೇ ಮಾಡಿದ ಕ್ಲೇಮ್ ನಂತರ ಉಳಿದಿರುವುದು.',
  'policy.remaining.assumed':
    'ಈ ವರ್ಷ ಯಾವ ಕ್ಲೇಮ್ ಆಗಿಲ್ಲ ಎಂದು ನಾವು ಭಾವಿಸಿದ್ದೇವೆ. ನೀವು ಈಗಾಗಲೇ ಕ್ಲೇಮ್ ಮಾಡಿದ್ದರೆ ಇದನ್ನು ಸರಿಪಡಿಸಿ: ಇದರಿಂದ ಪ್ರತಿ ಅಂದಾಜೂ ಬದಲಾಗುತ್ತದೆ.',
  'policy.remaining.restore':
    'ಕವರ್ ಮುಗಿದರೆ ನಿಮ್ಮ ಪಾಲಿಸಿ ಅದನ್ನು ವರ್ಷಕ್ಕೆ ಒಮ್ಮೆ ಮತ್ತೆ ತುಂಬಿಸುತ್ತದೆ.',
  'policy.room': 'ಕವರ್ ಇರುವ ಕೊಠಡಿ',
  'policy.room.hint': 'ದಿನದ ಮೊತ್ತ, 1% ನಂತಹ ಶೇಕಡಾ, ಕೊಠಡಿಯ ದರ್ಜೆ, ಅಥವಾ "ಮಿತಿ ಇಲ್ಲ"',
  'policy.room.note':
    'ದುಬಾರಿ ಕೊಠಡಿ ತೆಗೆದುಕೊಂಡರೆ ಶಸ್ತ್ರಚಿಕಿತ್ಸಕ, ಶಸ್ತ್ರಚಿಕಿತ್ಸಾ ಕೊಠಡಿ ಮತ್ತು ಶುಶ್ರೂಷೆಯ ಖರ್ಚಿನಲ್ಲೂ ವಿಮಾ ಕಂಪನಿ ಕಡಿಮೆ ಕೊಡುತ್ತದೆ.',
  'policy.copay': 'ಪ್ರತಿ ಕ್ಲೇಮ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಪಾಲು',
  'policy.copay.none': 'ಇಲ್ಲ',
  'policy.copay.hint': 'ಶೇಕಡಾವಾರು, ಉದಾ 10. ಇಲ್ಲದಿದ್ದರೆ 0 ಬರೆಯಿರಿ.',
  'policy.copay.age':
    '{age} ವರ್ಷ ಮತ್ತು ಅದಕ್ಕಿಂತ ಮೇಲಿನ ಸದಸ್ಯರಿಗೆ ಮಾತ್ರ. ಅದಕ್ಕಿಂತ ಚಿಕ್ಕ ಸದಸ್ಯರ ಕ್ಲೇಮ್‌ಗೆ ಯಾವ ಪಾಲೂ ಇಲ್ಲ.',
  'policy.icu': 'ICU ಕವರ್',
  'policy.deductible': 'ಮೊದಲು ನೀವು ಕೊಡುವುದು',
  'policy.deductible.none': 'ಏನೂ ಇಲ್ಲ',
  'policy.deductible.hint':
    'ಇದು ಟಾಪ್-ಅಪ್ ಪಾಲಿಸಿಗಳಲ್ಲಿ ಮಾತ್ರ ಇರುತ್ತದೆ. ನಿಮ್ಮಲ್ಲಿ ಇಲ್ಲದಿದ್ದರೆ 0 ಬರೆಯಿರಿ.',
  'policy.deductible.note':
    'ಇದು ಟಾಪ್-ಅಪ್ ಪಾಲಿಸಿ. ಇದು ಈ ಮೊತ್ತಕ್ಕಿಂತ ಮೇಲಿನದನ್ನು ಮಾತ್ರ ಕೊಡುತ್ತದೆ.',
  'policy.consumables': 'ಬಳಕೆಯ ಸಾಮಗ್ರಿ',
  'policy.covered': 'ಕವರ್ ಇದೆ',
  'policy.not_covered': 'ಕವರ್ ಇಲ್ಲ',
  'policy.consumables.note': 'ಕೈಗವಸು, ಸಿರಿಂಜ್ ಮತ್ತು ಅಂತಹ ವಸ್ತುಗಳನ್ನು ನೀವೇ ಕೊಡಬೇಕು.',
  'policy.daycare': 'ಒಂದು ದಿನಕ್ಕಿಂತ ಕಡಿಮೆಯ ಚಿಕಿತ್ಸೆ',
  'policy.not_stated': 'ಬರೆದಿಲ್ಲ',
  'policy.daycare.no':
    'ಕವರ್‌ಗೆ ಪೂರ್ಣ ಒಂದು ದಿನದ ದಾಖಲಾತಿ ಬೇಕು. ಕಣ್ಣಿನ ಪೊರೆ, ಡಯಾಲಿಸಿಸ್ ಮುಂತಾದ ಚಿಕಿತ್ಸೆಗಳಿಗೆ ಹಣ ಸಿಗುವುದಿಲ್ಲ.',
  'policy.daycare.unknown':
    'ನಿಮ್ಮ ದಾಖಲೆಯಲ್ಲಿ ಇದು ಬರೆದಿಲ್ಲ. ಕೇಳಿಕೊಳ್ಳುವುದು ಒಳ್ಳೆಯದು, ಏಕೆಂದರೆ ಕವರ್‌ಗೆ ಸಾಮಾನ್ಯವಾಗಿ 24 ಗಂಟೆಗಳ ದಾಖಲಾತಿ ಬೇಕಾಗುತ್ತದೆ.',
  'policy.sublimits': 'ಪ್ರತ್ಯೇಕ ಮಿತಿಗಳು',
  'policy.continue': 'ಕವರ್ ಇರುವ ಆಸ್ಪತ್ರೆಗಳನ್ನು ತೋರಿಸಿ',
  'policy.to_confirm': '{count} ದೃಢಪಡಿಸಬೇಕು',
  'policy.from_scan': 'ಸ್ಕ್ಯಾನ್‌ನಿಂದ ಓದಲಾಗಿದೆ',
  'policy.read_cleanly': 'ಸ್ಪಷ್ಟವಾಗಿ ಓದಲಾಗಿದೆ',

  'scheme.cover': 'ಈ ವರ್ಷದ ಕವರ್',
  'scheme.cover.note': 'ವರ್ಷಕ್ಕೆ, ಇಡೀ ಕುಟುಂಬಕ್ಕೆ ಸೇರಿ.',
  'scheme.you_pay': 'ಪಟ್ಟಿಯಲ್ಲಿರುವ ಆಸ್ಪತ್ರೆಯಲ್ಲಿ ನೀವು ಎಷ್ಟು ಕೊಡುತ್ತೀರಿ',
  'scheme.you_pay.value': 'ಏನೂ ಇಲ್ಲ',
  'scheme.you_pay.note':
    'ಚಿಕಿತ್ಸೆಯನ್ನು ನಿಗದಿತ ಪ್ಯಾಕೇಜ್ ದರದಲ್ಲಿ ಪಡೆಯಲಾಗುತ್ತದೆ. ಬಿಲ್ ಕಟ್ಟುವುದೂ ಇಲ್ಲ, ಕ್ಲೇಮ್ ಮಾಡುವುದೂ ಇಲ್ಲ.',
  'scheme.room': 'ಒಳಗೊಂಡಿರುವ ಕೊಠಡಿ',
  'scheme.room.note':
    'ಇದಕ್ಕಿಂತ ದೊಡ್ಡ ಕೊಠಡಿ ನಿಮ್ಮ ಸ್ವಂತ ಖರ್ಚಿನಲ್ಲಿ, ಆದರೆ ಅದರಿಂದ ಬೇರೆ ಯಾವುದರ ಕವರ್ ಕೂಡ ಕಡಿಮೆಯಾಗುವುದಿಲ್ಲ.',
  'scheme.consumables': 'ಸಾಮಗ್ರಿ, ಇಂಪ್ಲಾಂಟ್, ಔಷಧಿ, ಪರೀಕ್ಷೆಗಳು',
  'scheme.consumables.value': 'ಪ್ಯಾಕೇಜ್‌ನಲ್ಲಿ ಸೇರಿದೆ',
  'scheme.empanelled_only':
    '{scheme} ಗಾಗಿ ಪಟ್ಟಿಯಲ್ಲಿರುವ ಆಸ್ಪತ್ರೆಯಲ್ಲಿ ಮಾತ್ರ ಇದು ಕೆಲಸ ಮಾಡುತ್ತದೆ. ಬೇರೆಡೆ ಈ ಯೋಜನೆ ಏನನ್ನೂ ಕೊಡುವುದಿಲ್ಲ, ಆಮೇಲೆ ಕ್ಲೇಮ್ ಕೂಡ ಇಲ್ಲ. ನಾವು ತೋರಿಸುವ ಆಸ್ಪತ್ರೆಗಳನ್ನು ಇದೇ ಆಧಾರದ ಮೇಲೆ ಆರಿಸಲಾಗಿದೆ.',

  'second.title': 'ನಿಮ್ಮ ಎರಡನೇ ಪಾಲಿಸಿ',
  'second.remove': 'ತೆಗೆದುಹಾಕಿ',
  'second.cover': 'ಕವರ್',
  'second.room': 'ಕೊಠಡಿ',
  'second.above': 'ಇದಕ್ಕಿಂತ ಮೇಲಿನದನ್ನು ಮಾತ್ರ ಕೊಡುತ್ತದೆ',
  'second.topup.how':
    'ಟಾಪ್-ಅಪ್ ಎಂದರೆ ಮೇಲಿನ ಮಿತಿಯವರೆಗಿನ ಕವರ್ ಆದ ಮೇಲೆ ಉಳಿಯುವುದನ್ನು ಕೊಡುವುದು. ನಾವು ಮೊದಲು ನಿಮ್ಮ ಮೊದಲ ಪಾಲಿಸಿಯನ್ನು ಲೆಕ್ಕಕ್ಕೆ ತೆಗೆದುಕೊಂಡು, ಉಳಿದ ಮೊತ್ತಕ್ಕೆ ಇದನ್ನು ಬಳಸುತ್ತೇವೆ.',
  'second.how':
    'ನಾವು ಒಂದು ಪಾಲಿಸಿಯನ್ನು ಲೆಕ್ಕಕ್ಕೆ ತೆಗೆದುಕೊಂಡು, ಉಳಿದ ಮೊತ್ತವನ್ನು ಇನ್ನೊಂದಕ್ಕೆ ಹಾಕುತ್ತೇವೆ, ಮತ್ತು ಯಾವ ಕ್ರಮದಲ್ಲಿ ನಿಮ್ಮ ಖರ್ಚು ಕಡಿಮೆ ಎಂದು ಹೇಳುತ್ತೇವೆ.',
  'second.add': '+ ನನ್ನ ಬಳಿ ಇನ್ನೊಂದು ಪಾಲಿಸಿ ಇದೆ',
  'second.add.why':
    'ಉದ್ಯೋಗದ ಕವರ್, ಅಥವಾ ಟಾಪ್-ಅಪ್. ಎರಡನೇ ಪಾಲಿಸಿ ಮೊದಲನೆಯದು ಬಿಟ್ಟದ್ದನ್ನು ಕೊಡುತ್ತದೆ, ಮತ್ತು ಬಹಳಷ್ಟು ಜನ ಅದರಿಂದ ಕ್ಲೇಮೇ ಮಾಡುವುದಿಲ್ಲ.',
  'second.other': 'ನಿಮ್ಮ ಇನ್ನೊಂದು ಪಾಲಿಸಿ',
  'second.cancel': 'ಬೇಡ',
  'second.form.insurer': 'ಇದು ಯಾರ ಜೊತೆ?',
  'second.form.insurer.hint': 'ವಿಮಾ ಕಂಪನಿಯ ಹೆಸರು, ಅಥವಾ ನಿಮ್ಮ ಕಚೇರಿಯದು.',
  'second.form.insurer.placeholder': 'ಉದಾ ನನ್ನ ಕಚೇರಿಯ ಗುಂಪು ಪಾಲಿಸಿ',
  'second.form.cover': 'ಎಷ್ಟು ಕವರ್?',
  'second.form.room': 'ಕೊಠಡಿ ಬಾಡಿಗೆ ಮಿತಿ',
  'second.form.room.none': 'ಮಿತಿ ಇಲ್ಲ',
  'second.form.room.flat': 'ದಿನಕ್ಕೆ ನಿಗದಿತ ಮೊತ್ತ',
  'second.form.room.amount': 'ದಿನದ ಮೊತ್ತ',
  'second.form.deductible': 'ಇದು ಒಂದು ಮೊತ್ತಕ್ಕಿಂತ ಮೇಲಿನದನ್ನು ಮಾತ್ರ ಕೊಡುತ್ತದೆಯೇ?',
  'second.form.deductible.hint':
    'ಟಾಪ್-ಅಪ್ ಪಾಲಿಸಿಗಳು ಹಾಗೆ ಮಾಡುತ್ತವೆ. ನಿಮ್ಮದು ಮಾಡದಿದ್ದರೆ 0 ಇರಲಿ.',
  'second.form.adding': 'ಸೇರಿಸಲಾಗುತ್ತಿದೆ…',
  'second.form.submit': 'ಈ ಪಾಲಿಸಿ ಸೇರಿಸಿ',

  'insured.title': 'ಯಾರ್ಯಾರಿಗೆ ಕವರ್ ಇದೆ',
  'insured.period': '{from} ರಿಂದ {to} ವರೆಗಿನ ಕವರ್',
  'insured.period.open': '{from} ರಿಂದ ಕವರ್',
  'insured.ending':
    'ಈ ಪಾಲಿಸಿ ವರ್ಷ {days} ದಿನಗಳಲ್ಲಿ ಮುಗಿಯುತ್ತದೆ. ನವೀಕರಣದ ನಂತರ ನಿಮ್ಮ ಕವರ್ ಮತ್ತೆ ಶುರುವಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ಆ ದಿನಾಂಕದ ಆಚೀಚಿನ ದಾಖಲಾತಿ ಬೇರೆ ಬೇರೆ ವರ್ಷದ ಕವರ್ ಮೇಲೆ ಹೋಗುತ್ತದೆ.',
  'insured.ended':
    'ಈ ಪಾಲಿಸಿ ವರ್ಷ ಮುಗಿದಿದೆ. ಈ ಅಂಕಿಗಳನ್ನು ನಂಬುವ ಮೊದಲು ನವೀಕರಣ ಆಗಿತ್ತೇ ಎಂದು ನೋಡಿ.',

  'waiting.title': 'ಕಾಯುವ ಅವಧಿ',
  'waiting.served': 'ಮುಗಿದಿದೆ. {date} ರಿಂದ ಕವರ್ ಇದೆ.',
  'waiting.from': '{date} ರಿಂದ ಕವರ್.',
  'waiting.no_start':
    'ಈ ಪಾಲಿಸಿ ಯಾವಾಗ ಶುರುವಾಯಿತು ಎಂಬುದನ್ನು ನಮಗೆ ಓದಲಾಗಲಿಲ್ಲ, ಆದ್ದರಿಂದ ಇವು ಈಗಲೂ ಅನ್ವಯಿಸುತ್ತವೆಯೇ ಎಂದು ಹೇಳಲಾಗುವುದಿಲ್ಲ. ಚಿಕಿತ್ಸೆ ಆರಿಸಿದಾಗ ನಿಮ್ಮನ್ನು ಕೇಳಲಾಗುತ್ತದೆ.',
  'waiting.pending':
    'ತೋರಿಸಿದ ದಿನಾಂಕದ ಮೊದಲು ಮಾಡಿದ ಕ್ಲೇಮ್ ತಿರಸ್ಕೃತವಾಗುತ್ತದೆ. ನೀವು ಆರಿಸುವ ಚಿಕಿತ್ಸೆಗೆ ತಕ್ಕಂತೆ ನಾವು ಇದನ್ನು ಪರಿಶೀಲಿಸುತ್ತೇವೆ.',

  'fact.correct.label': '{field} ಸರಿಪಡಿಸಿ',
  'fact.correct': 'ಇದನ್ನು ಸರಿಪಡಿಸಿ',
  'fact.saving': 'ಉಳಿಸಲಾಗುತ್ತಿದೆ…',
  'fact.save': 'ಉಳಿಸಿ',
  'fact.cancel': 'ಬೇಡ',

  'ask.placeholder.percent': 'ಉದಾ 10%, ಅಥವಾ ಹತ್ತು ಶೇಕಡಾ',
  'ask.placeholder.amount': 'ಉದಾ 5 ಲಕ್ಷ, 5,00,000, ಅಥವಾ ಮಿತಿ ಇಲ್ಲ',
  'ask.confirming': 'ಒಮ್ಮೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳೋಣ',
  'ask.title': 'ನಿಮ್ಮಿಂದ ಒಂದು ವಿಷಯ ತಿಳಿಯಬೇಕು',
  'ask.remaining': 'ಇದರ ನಂತರ ಇನ್ನೂ {count}',
  'ask.page': 'ನಾವು ನಿಮ್ಮ ದಾಖಲೆಯ ಪುಟ {page} ನೋಡುತ್ತಿದ್ದೆವು.',
  'ask.source.page': '{source} ಇಂದ, ಪುಟ {page}',
  'ask.source': '{source} ಇಂದ',
  'ask.other': 'ಇವುಗಳಲ್ಲಿ ಯಾವುದೂ ಅಲ್ಲ, ನಾನೇ ಹೇಳುತ್ತೇನೆ',
  'ask.reading': 'ಓದಲಾಗುತ್ತಿದೆ…',
  'ask.confirm': 'ಖಚಿತಪಡಿಸಿ',
  'ask.free_text':
    'ನಿಮ್ಮ ದಾಖಲೆಯಲ್ಲಿ ಇರುವಂತೆಯೇ ಬರೆಯಿರಿ, ಪದಗಳಲ್ಲಿ ಅಥವಾ ಅಂಕಿಗಳಲ್ಲಿ. ಬಳಸುವ ಮೊದಲು ನಾವು ಅದನ್ನು ನಿಮಗೆ ಓದಿ ತೋರಿಸುತ್ತೇವೆ.',
  'ask.skip': 'ಇದು ನನಗೆ ಗೊತ್ತಿಲ್ಲ',
  'ask.skip.hint': 'ನಾವು ಮುಂದುವರಿಯುತ್ತೇವೆ ಮತ್ತು ಖಚಿತವಿಲ್ಲದಲ್ಲಿ ಹಾಗೆಂದು ಹೇಳುತ್ತೇವೆ.',

  'evidence.title': 'ಈ ಅಂಕಿಗಳು ಎಲ್ಲಿಂದ ಬಂದವು',
  'evidence.count': 'ನಿಮ್ಮ ದಾಖಲೆಯಿಂದ ಓದಿದ {count} ಭಾಗಗಳು',
  'evidence.hide': 'ಮರೆಮಾಡಿ',
  'evidence.show': 'ನೋಡಿ',
  'evidence.page': 'ಪುಟ {page}',
  'evidence.uncertain': 'ಖಚಿತವಿಲ್ಲ',

  'search.title': 'ನಿಮಗೆ ಯಾವ ಚಿಕಿತ್ಸೆ ಬೇಕು?',
  'search.subtitle':
    'ಅದನ್ನು ಮಾಡುವ ಆಸ್ಪತ್ರೆಗಳನ್ನು ನಾವು ಹುಡುಕುತ್ತೇವೆ, ಮತ್ತು ಪ್ರತಿಯೊಂದರಲ್ಲೂ ನೀವು ಎಷ್ಟು ಕೊಡಬೇಕು ಎಂದು ಹೇಳುತ್ತೇವೆ.',
  'search.treatment': 'ಚಿಕಿತ್ಸೆ',
  'search.treatment.hint':
    'ನಿಮಗೆ ಹೇಳಿದ್ದನ್ನೇ ಬರೆಯಿರಿ. ಅದನ್ನು ನಾವು ಹತ್ತಿರದ ಚಿಕಿತ್ಸೆಗೆ ಹೊಂದಿಸುತ್ತೇವೆ, ಅದರ ಖರ್ಚನ್ನು ನಾವು ಲೆಕ್ಕ ಹಾಕಬಲ್ಲೆವು.',
  'search.patient': 'ಯಾರಿಗೆ ಚಿಕಿತ್ಸೆ?',
  'search.patient.hint':
    'ನಿಮ್ಮ ಪಾಲಿಸಿ ಹಿರಿಯ ಸದಸ್ಯರ ಮೇಲೆ ಮಾತ್ರ ಪಾಲು ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ, ಆದ್ದರಿಂದ ಇದರಿಂದ ಅಂಕಿಗಳು ಬದಲಾಗುತ್ತವೆ.',
  'search.patient.unsure': 'ಇನ್ನೂ ಖಚಿತವಿಲ್ಲ',
  'search.city': 'ನಗರ',
  'search.city.count': '{city} ({count} ಆಸ್ಪತ್ರೆಗಳು)',
  'search.distance': 'ನೀವು ಎಷ್ಟು ದೂರ ಹೋಗಬಲ್ಲಿರಿ?',
  'search.distance.upto': '{km} ಕಿಮೀವರೆಗೆ',
  'search.preference': 'ನಿಮಗೆ ಅತ್ಯಂತ ಮುಖ್ಯವಾದದ್ದು ಏನು?',
  'search.urgency': 'ಎಷ್ಟು ಬೇಗ?',
  'search.urgency.planned': 'ಮೊದಲೇ ನಿಗದಿ',
  'search.urgency.urgent': 'ಕೆಲವೇ ದಿನಗಳಲ್ಲಿ',
  'search.urgency.emergency': 'ತುರ್ತು',
  'search.searching': 'ಹುಡುಕಲಾಗುತ್ತಿದೆ…',
  'search.go': 'ನನ್ನ ಆಯ್ಕೆಗಳನ್ನು ತೋರಿಸಿ',

  'preference.protect_money': 'ನನ್ನ ಖರ್ಚು ಕಡಿಮೆ ಇರಲಿ',
  'preference.best_care': 'ಅತ್ಯುತ್ತಮ ಸೌಲಭ್ಯದ ಆಸ್ಪತ್ರೆ',
  'preference.nearest': 'ಬೇಗ ತಲುಪುವಂತಿರಲಿ',
  'preference.balanced': 'ಸಮತೋಲಿತ',

  'eligibility.declined': 'ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ಈ ಕ್ಲೇಮ್ ತಿರಸ್ಕರಿಸುತ್ತದೆ',
  'eligibility.declined.hint': 'ಕೆಳಗಿನ ಖರ್ಚುಗಳನ್ನು ನೀವೇ ಕೊಡಬೇಕಾಗುತ್ತದೆ.',
  'eligibility.one_answer': 'ಒಂದು ಉತ್ತರದಿಂದ ಇದು ಇತ್ಯರ್ಥವಾಗುತ್ತದೆ.',
  'eligibility.why_ask':
    'ಯಾವ ಪಾಲಿಸಿಯಲ್ಲೂ ಇದು ಬರೆದಿಲ್ಲ, ಮತ್ತು ಇದರಿಂದ ಉತ್ತರ ಬದಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ಕೇಳಬೇಕಾಗಿದೆ. ನಿಮ್ಮ ಉತ್ತರ ಈ ಸಾಧನದಲ್ಲೇ ಉಳಿಯುತ್ತದೆ.',
  'eligibility.had_before': 'ಹೌದು, ಇದು ಮೊದಲಿನಿಂದ ಇತ್ತು',
  'eligibility.came_after': 'ಇಲ್ಲ, ಇದು ಆಮೇಲೆ ಬಂತು',
  'eligibility.accident': 'ಇದು ಅಪಘಾತ',

  'results.looked_at.city': 'ನಾವು {city} ದ {count} ಆಸ್ಪತ್ರೆಗಳನ್ನು ನೋಡಿದೆವು.',
  'results.looked_at': 'ನಾವು {count} ಆಸ್ಪತ್ರೆಗಳನ್ನು ನೋಡಿದೆವು.',
  'results.relaxed': 'ಇವು ಸಿಗಲು ನಾವು ನಿಮ್ಮ ಷರತ್ತುಗಳನ್ನು ಸ್ವಲ್ಪ ಸಡಿಲಿಸಬೇಕಾಯಿತು',
  'results.excluded': 'ಉಳಿದ ಆಸ್ಪತ್ರೆಗಳು ಏಕೆ ಬಿಟ್ಟುಹೋದವು',
  'results.filter': 'ಹೆಸರು ಅಥವಾ ಪ್ರದೇಶದಿಂದ ಆಸ್ಪತ್ರೆ ಹುಡುಕಿ',
  'results.filter.label': 'ಈ ಫಲಿತಾಂಶಗಳನ್ನು ಆಸ್ಪತ್ರೆಯ ಹೆಸರು ಅಥವಾ ಪ್ರದೇಶದಿಂದ ಶೋಧಿಸಿ',
  'results.filter.none': '"{query}" ಗೆ ಇಲ್ಲಿ ಯಾವ ಆಸ್ಪತ್ರೆಯೂ ಸಿಗಲಿಲ್ಲ.',
  'results.filter.some': '{total} ರಲ್ಲಿ {shown} "{query}" ಗೆ ಹೊಂದುತ್ತವೆ.',
  'results.strong': 'ಒಳ್ಳೆಯ ಆಯ್ಕೆ',
  'results.travel': 'ಸುಮಾರು {minutes} ನಿಮಿಷ',
  'results.you_would_pay': 'ನೀವು ಕೊಡುವುದು',
  'results.up_to': 'ಗರಿಷ್ಠ',
  'results.up_to.driver': '{driver} ಆದರೆ',
  'results.hospital_bill': 'ಆಸ್ಪತ್ರೆಯ ಬಿಲ್',
  'results.insurer_pays_short': 'ವಿಮಾ ಕಂಪನಿ ಕೊಡುತ್ತದೆ',
  'results.upfront': 'ಮೊದಲು ನೀವು ಕೊಡಬೇಕು',
  'results.settlement': 'ಪಾವತಿ ವಿಧಾನ',
  'results.room': 'ಕೊಠಡಿ',
  'results.room.rate': '{room}, ದಿನಕ್ಕೆ {rate}',
  'results.hide_breakdown': 'ವಿವರ ಮರೆಮಾಡಿ',
  'results.show_breakdown': 'ನನ್ನ ಹಣ ಎಲ್ಲಿಗೆ ಹೋಗುತ್ತದೆ?',
  'results.track': 'ನನ್ನ ಚಿಕಿತ್ಸೆಯನ್ನು ಇಲ್ಲೇ ನೋಡಿ',

  'exclusion.too_far': 'ನಿಮ್ಮ ದೂರದ ಮಿತಿಯ ಹೊರಗೆ',
  'exclusion.procedure_unavailable': 'ಈ ಚಿಕಿತ್ಸೆ ಮಾಡುವುದಿಲ್ಲ',
  'exclusion.specialty_unavailable': 'ಈ ವಿಭಾಗ ಇಲ್ಲ',
  'exclusion.not_cashless': 'ನಿಮ್ಮ ನಗದುರಹಿತ ಜಾಲದಲ್ಲಿ ಇಲ್ಲ',
  'exclusion.no_bed_available': 'ಈಗ ಹಾಸಿಗೆ ಖಾಲಿ ಇಲ್ಲ',
  'exclusion.no_eligible_room': 'ನಿಮ್ಮ ದರ್ಜೆಯ ಕೊಠಡಿ ಇಲ್ಲ',
  'exclusion.scheme_not_empanelled': 'ನಿಮ್ಮ ಯೋಜನೆಗೆ ಪಟ್ಟಿಯಲ್ಲಿ ಇಲ್ಲ',

  'room.general_ward': 'ಸಾಮಾನ್ಯ ವಾರ್ಡ್',
  'room.twin_sharing': 'ಇಬ್ಬರ ಕೊಠಡಿ',
  'room.single_private': 'ಏಕವ್ಯಕ್ತಿ ಕೊಠಡಿ',
  'room.deluxe': 'ಡೀಲಕ್ಸ್ ಕೊಠಡಿ',
  'room.suite': 'ಸೂಟ್',
  'room.icu': 'ICU',

  'settlement.cashless': 'ನಗದುರಹಿತ',
  'settlement.reimbursement': 'ಮೊದಲು ನೀವೇ ಕೊಡಿ, ಆಮೇಲೆ ಕ್ಲೇಮ್ ಮಾಡಿ',
  'settlement.scheme_package': 'ಯೋಜನೆಯ ಪ್ಯಾಕೇಜ್',

  'waterfall.title': 'ಆಸ್ಪತ್ರೆಯ ಬಿಲ್‌ನಿಂದ ನೀವು ಕೊಡುವವರೆಗೆ',
  'waterfall.lines': 'ಆಸ್ಪತ್ರೆಯ ಬಿಲ್, ಒಂದೊಂದಾಗಿ',

  'journey.title': 'ನಿಮ್ಮ ಚಿಕಿತ್ಸೆ',
  'journey.per_day': 'ದಿನಕ್ಕೆ ₹{amount}',
  'journey.preauth.file': 'ಪೂರ್ವ-ಅನುಮೋದನೆ ಸಲ್ಲಿಸಲಾಗಿದೆ ಎಂದು ಗುರುತಿಸಿ',
  'journey.timeline.skipped': '{stages} ಬಿಟ್ಟುಬಿಡಲಾಗಿದೆ.',
  'journey.charges.count': '{count} ದಾಖಲು, ಒಟ್ಟು {total}',
  'journey.charge.options': '{head} ಗಾಗಿ ಆಯ್ಕೆಗಳು',
  'journey.charge.close_menu': 'ಪಟ್ಟಿ ಮುಚ್ಚಿ',
  'journey.charge.edit': 'ಬದಲಾಯಿಸಿ',
  'journey.charge.delete': 'ಅಳಿಸಿ',
  'journey.charge.head': 'ಇದು ಯಾವುದಕ್ಕಾಗಿ?',
  'journey.charge.amount': 'ಮೊತ್ತ',
  'journey.charge.when': 'ಯಾವಾಗ',
  'journey.charge.save': 'ಉಳಿಸಿ',
  'journey.charge.cancel': 'ಮುಚ್ಚಿ',
  'journey.charge.new_day': 'ಇದು ಚಿಕಿತ್ಸೆಯ ಹೊಸ ದಿನ',
  'journey.charge.add': 'ಖರ್ಚು ಸೇರಿಸಿ',
  'journey.add_charge.hint':
    'ಬಿಲ್‌ಗಳು ಬಂದಂತೆ ದಾಖಲಿಸುತ್ತಾ ಹೋಗಿ, ಅಂದಾಜು ಸರಿಯಾಗಿ ಉಳಿಯುತ್ತದೆ.',
  'journey.receipt.too_large':
    'ಈ ಕಡತ {size} MB ಇದೆ. ನಾವು ಗರಿಷ್ಠ {limit} MB ತೆಗೆದುಕೊಳ್ಳಬಹುದು.',
  'journey.receipt.remove': 'ತೆಗೆದುಹಾಕಿ',
  'journey.receipt.attach': 'ಬಿಲ್ ಅಥವಾ ರಸೀದಿ ಲಗತ್ತಿಸಿ (ಕಡ್ಡಾಯವಲ್ಲ)',
  'journey.checklist.count': '{total} ರಲ್ಲಿ {done}',
  'journey.checklist.now': 'ಈಗ',
  'journey.position.you_pay': 'ಇಲ್ಲಿಯವರೆಗೆ ನೀವು ಕೊಡುವುದು',
  'journey.position.split':
    'ಆಸ್ಪತ್ರೆ {billed} ಬಿಲ್ ಮಾಡಿದೆ. ಅದರಲ್ಲಿ {covered} ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ಕೊಡುತ್ತದೆ.',
  'journey.position.hide': 'ವ್ಯತ್ಯಾಸ ಎಲ್ಲಿಂದ ಬರುತ್ತದೆ ಎಂಬುದನ್ನು ಮರೆಮಾಡಿ',
  'journey.position.show': 'ವ್ಯತ್ಯಾಸ ಎಲ್ಲಿಂದ ಬರುತ್ತದೆ ಎಂಬುದನ್ನು ನೋಡಿ',
  'journey.burn.used': 'ಇಲ್ಲಿಯವರೆಗೆ ಬಳಸಿದ ಕವರ್',
  'journey.burn.of': '{total} ರಲ್ಲಿ {used}',
  'journey.burn.left': '{amount} ಉಳಿದಿದೆ',
  'journey.burn.rate': 'ದಿನಕ್ಕೆ {amount}',
  'journey.burn.reached': 'ಕವರ್ ಇಂದೇ ಮುಗಿದಿದೆ',
  'journey.burn.days_left': 'ಸುಮಾರು {days} ದಿನಗಳ ಕವರ್ ಉಳಿದಿದೆ',
  'journey.advance.settled': 'ನಿಮ್ಮ ಕ್ಲೇಮ್ ಇತ್ಯರ್ಥವಾಗಿದೆ',
  'journey.advance.title': 'ಈಗ ನೀವು ಎಲ್ಲಿದ್ದೀರಿ?',
  'journey.advance.settled.hint': 'ಏನಾದರೂ ಬದಲಾದರೆ ನೀವು ಈಗಲೂ ಹಿಂದಿನ ಹಂತಕ್ಕೆ ಹೋಗಬಹುದು.',
  'journey.advance.hint':
    'ವಿಷಯ ಮುಂದುವರಿದಂತೆ ಇದನ್ನು ಬದಲಾಯಿಸುತ್ತಿರಿ. ನೀವು ಯಾವಾಗ ಬೇಕಾದರೂ ಹಿಂದೆ ಹೋಗಬಹುದು.',
  'journey.advance.stage': 'ಹಂತ',
  'journey.advance.here': 'ನೀವು ಇಲ್ಲಿದ್ದೀರಿ',
  'journey.advance.back': 'ಹಿಂದೆ ಹೋಗಿ',
  'journey.advance.back.hint':
    'ಇದರಿಂದ ನಿಮ್ಮ ಚಿಕಿತ್ಸೆ {stage} ಗೆ ಹಿಂತಿರುಗುತ್ತದೆ. ನೀವು ದಾಖಲಿಸಿದ್ದು ಏನೂ ಹೋಗುವುದಿಲ್ಲ.',
  'journey.advance.go_back': 'ಈ ಹಂತಕ್ಕೆ ಹಿಂತಿರುಗಿ',
  'journey.advance.update': 'ನವೀಕರಿಸಿ',
  'journey.skip.cancel': 'ಬೇಡ',
  'journey.skip.title': 'ಒಂದು ಮಾತು',
  'journey.skip.body': 'ನೇರವಾಗಿ {stage} ಗೆ ಹೋದರೆ {skipped} ಬಿಟ್ಟುಹೋಗುತ್ತವೆ.',
  'journey.skip.reassure':
    'ಇದು ಹೆಚ್ಚಿನ ಬಾರಿ ಸರಿಯೇ. ಹಲವು ದಾಖಲಾತಿಗಳಲ್ಲಿ ಇವುಗಳಲ್ಲಿ ಕೆಲವು ಬರುವುದೇ ಇಲ್ಲ. ನಿಮ್ಮ ಅಂದಾಜು ಎರಡೂ ಸಂದರ್ಭದಲ್ಲಿ ಸರಿಯಾಗಿ ಉಳಿಯುತ್ತದೆ, ಮತ್ತು ನೀವು ಆಮೇಲೆ ಯಾವುದೇ ಹಂತಕ್ಕೆ ಹಿಂತಿರುಗಬಹುದು.',
  'journey.skip.note': 'ಕಾರಣ ಬರೆಯಲು ಬಯಸುತ್ತೇನೆ (ಕಡ್ಡಾಯವಲ್ಲ)',
  'journey.skip.placeholder':
    'ಉದಾ: ತುರ್ತು ಸ್ಥಿತಿಯಲ್ಲಿ ದಾಖಲಾಗಿದ್ದರಿಂದ ಪೂರ್ವ-ಅನುಮೋದನೆಗೆ ಸಮಯ ಸಿಗಲಿಲ್ಲ.',
  'journey.skip.confirm': '{stage} ಗೆ ಹೋಗಿ',
  'journey.skip.decline': 'ಈಗ ಬೇಡ',

  'head.room_rent': 'ಕೊಠಡಿ ಬಾಡಿಗೆ',
  'head.icu_charges': 'ICU ಶುಲ್ಕ',
  'head.investigations': 'ಪರೀಕ್ಷೆಗಳು ಮತ್ತು ಸ್ಕ್ಯಾನ್',
  'head.pharmacy': 'ಔಷಧಿಗಳು',
  'head.consumables': 'ಬಳಕೆಯ ಸಾಮಗ್ರಿ',
  'head.surgeon_fee': 'ಶಸ್ತ್ರಚಿಕಿತ್ಸಕರ ಶುಲ್ಕ',
  'head.ot_charges': 'ಶಸ್ತ್ರಚಿಕಿತ್ಸಾ ಕೊಠಡಿ',
  'head.nursing': 'ಶುಶ್ರೂಷೆ',
  'head.implants': 'ಇಂಪ್ಲಾಂಟ್‌ಗಳು',
  'head.non_medical': 'ವೈದ್ಯಕೀಯೇತರ ವಸ್ತುಗಳು',

  'list.a_stage': 'ಒಂದು ಹಂತ',
  'list.and': 'ಮತ್ತು',

  'bill.what_we_do':
    'ಒಂದೊಂದು ವಸ್ತುವಿನ ಬಿಲ್ ಕೇಳಿ, ಒಂದೇ ಸಾಲಿನ ಒಟ್ಟು ಮೊತ್ತ ಅಲ್ಲ, ಮತ್ತು ಅದರ ಫೋಟೋ ತೆಗೆಯಿರಿ. ನಾವು ಅದನ್ನು ಸಾಲು ಸಾಲಾಗಿ ಓದಿ, ಸಹಿ ಹಾಕುವ ಮೊದಲು ಏನನ್ನು ಕೇಳಬೇಕು ಎಂದು ಹೇಳುತ್ತೇವೆ: ನಿಯಂತ್ರಕರ ಪ್ರಕಾರ ಈಗಾಗಲೇ ಬೇರೊಂದು ಶುಲ್ಕದಲ್ಲಿ ಸೇರಿರುವ ವಸ್ತುಗಳು, ಎರಡು ಬಾರಿ ಬರೆದ ಸಾಲುಗಳು, ಗುಣಿಸಿದರೆ ಹೊಂದದ ಅಂಕಿಗಳು, ಮತ್ತು ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ಮಾಡುವ ಆದರೆ ಬಿಲ್ಲಿಂಗ್ ಕೌಂಟರ್ ಹೇಳದ ಕಡಿತ.',
  'bill.photo_hint':
    'ಎದುರಿನಿಂದ, ಒಳ್ಳೆಯ ಬೆಳಕಿನಲ್ಲಿ. ಬಿಲ್ಲಿಂಗ್ ಕೌಂಟರ್‌ನಿಂದ ಸಿಕ್ಕ PDF ನಿಖರವಾಗಿ ಓದುತ್ತದೆ.',
  'bill.settles_to.hint': 'ಅಂದಾಜಿನಲ್ಲಿದ್ದ ಅದೇ ಲೆಕ್ಕವನ್ನು ನಿಜವಾದ ಬಿಲ್‌ಗೆ ಅನ್ವಯಿಸಲಾಗಿದೆ.',
  'bill.col.line': 'ಕ್ರಮ',
  'bill.col.item': 'ವಸ್ತು',
  'bill.col.head': 'ಶೀರ್ಷಿಕೆ',
  'bill.col.amount': 'ಮೊತ್ತ',

  'settings.close': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳನ್ನು ಮುಚ್ಚಿ',
  'settings.close.short': 'ಮುಚ್ಚಿ',
  'settings.theme.label': 'ಬಣ್ಣ',
  'settings.theme.hint': '"ಸಿಸ್ಟಂ" ನಿಮ್ಮ ಫೋನ್ ಅಥವಾ ಕಂಪ್ಯೂಟರ್ ಪ್ರಕಾರ ನಡೆಯುತ್ತದೆ.',
  'settings.theme.light': 'ಬೆಳಕು',
  'settings.theme.dark': 'ಕತ್ತಲೆ',
  'settings.theme.system': 'ಸಿಸ್ಟಂ',
  'settings.text_size.hint':
    'ಇಡೀ ಆ್ಯಪ್‌ನಲ್ಲಿ ದೊಡ್ಡ ಅಕ್ಷರಗಳು, ಆತುರದಲ್ಲಿ ಫೋನ್‌ನಲ್ಲಿ ಓದಲು ಸಾಧ್ಯವಾಗುವಂತೆ.',
  'settings.text_size.default': 'ಸಾಮಾನ್ಯ',
  'settings.text_size.large': 'ದೊಡ್ಡದು',
  'settings.session': 'ಈ ಅವಧಿ',
  'settings.session.hint':
    'ನಿಮ್ಮ ಪಾಲಿಸಿ ಮತ್ತು ನಿಮಗಾಗಿ ಸಿಕ್ಕ ಆಸ್ಪತ್ರೆಗಳು ಈ ಟ್ಯಾಬ್ ತೆರೆದಿರುವವರೆಗೆ ಮಾತ್ರ ಇರುತ್ತವೆ. ಪುಟವನ್ನು ಮತ್ತೆ ಲೋಡ್ ಮಾಡಿದರೆ ಎಲ್ಲವೂ ಮೊದಲಿನಿಂದ.',
  'settings.clear.yes': 'ಹೌದು, ಅಳಿಸಿ',
  'settings.clear.no': 'ಇರಲಿ',
  'settings.clear': 'ಅಳಿಸಿ ಮೊದಲಿನಿಂದ ಶುರು ಮಾಡಿ',
  'settings.developer': 'ಡೆವಲಪರ್',
  'settings.developer.note':
    'ಪರಿಶೀಲನೆಗಾಗಿ. ಇಲ್ಲಿನ ಯಾವುದರಿಂದಲೂ ಆ್ಯಪ್‌ನ ಲೆಕ್ಕ ಬದಲಾಗುವುದಿಲ್ಲ.',
  'settings.activity': 'ಚಟುವಟಿಕೆ ಫಲಕ ತೋರಿಸಿ',
  'settings.activity.hint':
    'ಪ್ರತಿ ಹಂತದ ನೇರ ನೋಟ, ಸಮಯದೊಂದಿಗೆ. ಸರ್ವರ್ ತನ್ನ ಲಾಗ್‌ನಲ್ಲಿ ಬರೆಯುವ ಅದೇ ಘಟನೆಗಳು.',
  'settings.api': 'API',
  'settings.api.reachable': 'ಸಿಗುತ್ತಿದೆ',
  'settings.api.unreachable': 'ಸಿಗುತ್ತಿಲ್ಲ',
  'settings.reset': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳನ್ನು ಮೊದಲಿನಂತೆ ಮಾಡಿ',

  disclaimer:
    'ಈ ಅಂದಾಜುಗಳು ಮಾರ್ಗದರ್ಶನಕ್ಕಷ್ಟೇ. ಇದು ಕೋಟೇಶನ್ ಅಲ್ಲ, ಅನುಮೋದನೆ ಅಲ್ಲ, ವೈದ್ಯಕೀಯ ಸಲಹೆಯೂ ಅಲ್ಲ. ಎಲ್ಲ ಮೊತ್ತಗಳನ್ನು ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ಮತ್ತು ಆಸ್ಪತ್ರೆಯ ವಿಮಾ ಕೌಂಟರ್‌ನಲ್ಲಿ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.',
}
