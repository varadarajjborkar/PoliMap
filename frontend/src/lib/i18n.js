// Interface language.
//
// Scoped deliberately. What gets translated here is the interface's own words:
// navigation, buttons, headings, the fixed guidance this app wrote itself.
// What never gets translated is anything read out of somebody's policy. A
// clause paraphrased into another language and shown as what the document says
// is a claim about their cover that nobody has checked, and this whole system
// is built on not doing that.
//
// Call sites pass the English alongside the key:
//
//     t('journey.download', 'Download this stay')
//
// so the source stays readable, a missing translation renders English rather
// than a key, and there is no separate English file to drift from the JSX.
//
// Amounts are left alone. Rupees group the same way in every one of these
// languages, and a family reading a figure off this screen has to be able to
// point at the same figure on a bill.

export const LANGUAGES = [
  { code: 'en', endonym: 'English' },
  { code: 'hi', endonym: 'हिन्दी' },
  { code: 'kn', endonym: 'ಕನ್ನಡ' },
  { code: 'mr', endonym: 'मराठी' },
  { code: 'te', endonym: 'తెలుగు' },
]

export const LANGUAGE_CODES = LANGUAGES.map((language) => language.code)

const hi = {
  'nav.setup': 'तैयारी',
  'nav.stay': 'अस्पताल में',
  'nav.back.hospitals': 'अस्पतालों पर वापस',

  'signin.title': 'जानिए आपके अस्पताल के इलाज पर कितना खर्च आएगा',
  'signin.subtitle':
    'अपने इलाज सहेजने के लिए एक नाम चुनें। यह इसी डिवाइस पर रहता है।',
  'signin.name': 'हम आपको क्या कहकर बुलाएँ?',
  'signin.continue': 'आगे बढ़ें',
  'signin.no_account':
    'कोई पासवर्ड नहीं, कोई खाता नहीं। आपकी पहचान बताने वाली कोई जानकारी कहीं नहीं भेजी जाती, और इसी डिवाइस पर दूसरा नाम डालने से अलग, स्वतंत्र इलाज दिखते हैं।',
  'home.title': 'आपके इलाज',
  'home.new': 'नया इलाज शुरू करें',

  'step.upload': 'आपकी पॉलिसी',
  'step.policy': 'आपका कवर',
  'step.search': 'अस्पताल',
  'step.short.upload': 'पॉलिसी',
  'step.short.policy': 'कवर',
  'step.short.search': 'अस्पताल',

  'results.you_pay': 'आप देंगे',
  'results.insurer_pays': 'बीमा कंपनी देगी',

  'journey.stage.pre_admission': 'भर्ती से पहले',
  'journey.stage.admitted': 'अस्पताल में',
  'journey.stage.discharge_planning': 'घर जाने की तैयारी',
  'journey.stage.settled': 'दावा निपट गया',
  'journey.download': 'यह पूरा ब्यौरा डाउनलोड करें',
  'journey.download.why':
    'आपका कवर, अनुमान, अब तक का बिल, और क्या करना बाकी है। बीमा काउंटर पर ले जाने के लिए एक पन्ना।',
  'journey.charges': 'अब तक के खर्च',
  'journey.add_charge': 'खर्च जोड़ें',
  'journey.timeline': 'अब तक क्या हुआ',
  'journey.checklist': 'अभी क्या करना है',

  'bill.title': 'आखिरी बिल जाँचें',
  'bill.subtitle':
    'IRDAI की उन चीज़ों की सूची के हिसाब से जो कोई पॉलिसी नहीं देती, और आपके अपने कवर के हिसाब से।',
  'bill.upload': 'बिल की फ़ोटो लें या अपलोड करें',
  'bill.reading': 'बिल पढ़ा जा रहा है…',
  'bill.nothing': 'इस बिल में IRDAI सूची या आपकी पॉलिसी के हिसाब से कुछ खटका नहीं।',
  'bill.settles_to': 'इस बिल का हिसाब',
  'bill.show_lines': 'पढ़ी गई पंक्तियाँ दिखाएँ',
  'bill.hide_lines': 'पंक्तियाँ छिपाएँ',
  'bill.another': 'दूसरा बिल जाँचें',
  'bill.to_ask': 'पूछने लायक',
  'bill.nothing_to_raise': 'कुछ उठाने लायक नहीं',

  'settings.language': 'भाषा',
  'settings.language.hint':
    'यह ऐप की अपनी भाषा बदलता है। आपकी पॉलिसी से पढ़ी गई बातें उसी भाषा में रहती हैं जिसमें दस्तावेज़ है।',
  'settings.theme': 'दिखावट',
  'settings.text_size': 'अक्षरों का आकार',

  disclaimer:
    'ये अनुमान केवल मार्गदर्शन के लिए हैं। यह कोई कोटेशन, मंज़ूरी या चिकित्सकीय सलाह नहीं है। सभी रकमें अपनी बीमा कंपनी और अस्पताल के बीमा काउंटर से जाँच लें।',
}

const kn = {
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

  'settings.language': 'ಭಾಷೆ',
  'settings.language.hint':
    'ಇದು ಆ್ಯಪ್‌ನ ಸ್ವಂತ ಭಾಷೆಯನ್ನು ಬದಲಾಯಿಸುತ್ತದೆ. ನಿಮ್ಮ ಪಾಲಿಸಿಯಿಂದ ಓದಿದ ವಿಷಯ ದಾಖಲೆಯ ಭಾಷೆಯಲ್ಲೇ ಉಳಿಯುತ್ತದೆ.',
  'settings.theme': 'ನೋಟ',
  'settings.text_size': 'ಅಕ್ಷರದ ಗಾತ್ರ',

  disclaimer:
    'ಈ ಅಂದಾಜುಗಳು ಮಾರ್ಗದರ್ಶನಕ್ಕಷ್ಟೇ. ಇದು ಕೋಟೇಶನ್ ಅಲ್ಲ, ಅನುಮೋದನೆ ಅಲ್ಲ, ವೈದ್ಯಕೀಯ ಸಲಹೆಯೂ ಅಲ್ಲ. ಎಲ್ಲ ಮೊತ್ತಗಳನ್ನು ನಿಮ್ಮ ವಿಮಾ ಕಂಪನಿ ಮತ್ತು ಆಸ್ಪತ್ರೆಯ ವಿಮಾ ಕೌಂಟರ್‌ನಲ್ಲಿ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.',
}

const mr = {
  'nav.setup': 'तयारी',
  'nav.stay': 'रुग्णालयात',
  'nav.back.hospitals': 'रुग्णालयांकडे परत',

  'signin.title': 'तुमच्या रुग्णालयातील उपचारांना किती खर्च येईल हे जाणून घ्या',
  'signin.subtitle':
    'तुमचे उपचार जतन करण्यासाठी एक नाव निवडा. ते या उपकरणावरच राहते.',
  'signin.name': 'तुम्हाला काय म्हणून हाक मारावी?',
  'signin.continue': 'पुढे चला',
  'signin.no_account':
    'पासवर्ड नाही, खाते नाही. तुमची ओळख सांगणारी कोणतीही माहिती कुठेही पाठवली जात नाही, आणि या उपकरणावर दुसरे नाव टाकल्यास वेगळे, स्वतंत्र उपचार उघडतात.',
  'home.title': 'तुमचे उपचार',
  'home.new': 'नवीन उपचार सुरू करा',

  'step.upload': 'तुमची पॉलिसी',
  'step.policy': 'तुमचे कव्हर',
  'step.search': 'रुग्णालये',
  'step.short.upload': 'पॉलिसी',
  'step.short.policy': 'कव्हर',
  'step.short.search': 'रुग्णालये',

  'results.you_pay': 'तुम्ही भरणार',
  'results.insurer_pays': 'विमा कंपनी भरणार',

  'journey.stage.pre_admission': 'दाखल होण्यापूर्वी',
  'journey.stage.admitted': 'रुग्णालयात',
  'journey.stage.discharge_planning': 'घरी जाण्याची तयारी',
  'journey.stage.settled': 'दावा निकाली निघाला',
  'journey.download': 'हा संपूर्ण तपशील डाउनलोड करा',
  'journey.download.why':
    'तुमचे कव्हर, अंदाज, आतापर्यंतचे बिल, आणि अजून काय करायचे आहे. विमा काउंटरवर नेण्यासाठी एक पान.',
  'journey.charges': 'आतापर्यंतचा खर्च',
  'journey.add_charge': 'खर्च नोंदवा',
  'journey.timeline': 'आतापर्यंत काय झाले',
  'journey.checklist': 'आता काय करायचे',

  'bill.title': 'अंतिम बिल तपासा',
  'bill.subtitle':
    'कोणतीही पॉलिसी न देणाऱ्या वस्तूंच्या IRDAI यादीशी, आणि तुमच्या स्वतःच्या कव्हरशी तपासून.',
  'bill.upload': 'बिलाचा फोटो काढा किंवा अपलोड करा',
  'bill.reading': 'बिल वाचले जात आहे…',
  'bill.nothing': 'IRDAI यादी किंवा तुमच्या पॉलिसीच्या तुलनेत या बिलात काही खटकले नाही.',
  'bill.settles_to': 'या बिलाचा हिशेब',
  'bill.show_lines': 'वाचलेल्या ओळी दाखवा',
  'bill.hide_lines': 'ओळी लपवा',
  'bill.another': 'दुसरे बिल तपासा',
  'bill.to_ask': 'विचारण्यासारखे',
  'bill.nothing_to_raise': 'उपस्थित करण्यासारखे काही नाही',

  'settings.language': 'भाषा',
  'settings.language.hint':
    'हे ॲपची स्वतःची भाषा बदलते. तुमच्या पॉलिसीतून वाचलेला मजकूर कागदपत्राच्याच भाषेत राहतो.',
  'settings.theme': 'दिसणे',
  'settings.text_size': 'अक्षरांचा आकार',

  disclaimer:
    'हे अंदाज केवळ मार्गदर्शनासाठी आहेत. हे कोटेशन नाही, मंजुरी नाही, आणि वैद्यकीय सल्लाही नाही. सर्व रकमा तुमच्या विमा कंपनीकडून आणि रुग्णालयाच्या विमा काउंटरवर तपासून घ्या.',
}

const te = {
  'nav.setup': 'సిద్ధత',
  'nav.stay': 'ఆసుపత్రిలో',
  'nav.back.hospitals': 'ఆసుపత్రులకు తిరిగి',

  'signin.title': 'మీ ఆసుపత్రి చికిత్సకు ఎంత ఖర్చు అవుతుందో తెలుసుకోండి',
  'signin.subtitle':
    'మీ చికిత్సలను భద్రపరచడానికి ఒక పేరు ఎంచుకోండి. అది ఈ పరికరంలోనే ఉంటుంది.',
  'signin.name': 'మిమ్మల్ని ఏమని పిలవాలి?',
  'signin.continue': 'కొనసాగించండి',
  'signin.no_account':
    'పాస్‌వర్డ్ లేదు, ఖాతా లేదు. మీ గుర్తింపును తెలిపే ఏ సమాచారమూ ఎక్కడికీ పంపబడదు, మరియు ఈ పరికరంలో వేరే పేరు పెట్టితే వేరే, ప్రత్యేకమైన చికిత్సలు తెరుచుకుంటాయి.',
  'home.title': 'మీ చికిత్సలు',
  'home.new': 'కొత్త చికిత్స మొదలుపెట్టండి',

  'step.upload': 'మీ పాలసీ',
  'step.policy': 'మీ కవరేజీ',
  'step.search': 'ఆసుపత్రులు',
  'step.short.upload': 'పాలసీ',
  'step.short.policy': 'కవరేజీ',
  'step.short.search': 'ఆసుపత్రులు',

  'results.you_pay': 'మీరు చెల్లించేది',
  'results.insurer_pays': 'బీమా సంస్థ చెల్లించేది',

  'journey.stage.pre_admission': 'చేరక ముందు',
  'journey.stage.admitted': 'ఆసుపత్రిలో',
  'journey.stage.discharge_planning': 'ఇంటికి వెళ్ళే ఏర్పాటు',
  'journey.stage.settled': 'క్లెయిమ్ పరిష్కారమైంది',
  'journey.download': 'ఈ పూర్తి వివరాలు డౌన్‌లోడ్ చేయండి',
  'journey.download.why':
    'మీ కవరేజీ, అంచనా, ఇప్పటివరకు వచ్చిన బిల్లు, ఇంకా చేయవలసినవి. బీమా కౌంటర్‌కు తీసుకెళ్ళడానికి ఒకే పేజీ.',
  'journey.charges': 'ఇప్పటివరకు ఖర్చు',
  'journey.add_charge': 'ఖర్చు జోడించండి',
  'journey.timeline': 'ఇప్పటివరకు ఏమి జరిగింది',
  'journey.checklist': 'ఇప్పుడు ఏమి చేయాలి',

  'bill.title': 'చివరి బిల్లు తనిఖీ చేయండి',
  'bill.subtitle':
    'ఏ పాలసీ చెల్లించని వస్తువుల IRDAI జాబితాతో, మరియు మీ సొంత కవరేజీతో సరిచూసి.',
  'bill.upload': 'బిల్లు ఫోటో తీయండి లేదా అప్‌లోడ్ చేయండి',
  'bill.reading': 'బిల్లు చదువుతున్నాం…',
  'bill.nothing': 'IRDAI జాబితా లేదా మీ పాలసీతో పోలిస్తే ఈ బిల్లులో ఏదీ ఇబ్బందిగా కనిపించలేదు.',
  'bill.settles_to': 'ఈ బిల్లు లెక్క',
  'bill.show_lines': 'చదివిన పంక్తులు చూపించండి',
  'bill.hide_lines': 'పంక్తులు దాచండి',
  'bill.another': 'వేరే బిల్లు తనిఖీ చేయండి',
  'bill.to_ask': 'అడగవలసినవి',
  'bill.nothing_to_raise': 'లేవనెత్తవలసినది ఏదీ లేదు',

  'settings.language': 'భాష',
  'settings.language.hint':
    'ఇది యాప్ సొంత భాషను మారుస్తుంది. మీ పాలసీ నుండి చదివినది పత్రం భాషలోనే ఉంటుంది.',
  'settings.theme': 'రూపం',
  'settings.text_size': 'అక్షరాల పరిమాణం',

  disclaimer:
    'ఈ అంచనాలు మార్గదర్శనం కోసమే. ఇది కోట్ కాదు, ఆమోదం కాదు, వైద్య సలహా కాదు. అన్ని మొత్తాలను మీ బీమా సంస్థతో మరియు ఆసుపత్రి బీమా కౌంటర్‌లో నిర్ధారించుకోండి.',
}

const STRINGS = { hi, kn, mr, te }

// English is the source, so it has no table: a key with no translation renders
// the English the call site passed, which is also what a partially translated
// language does. Nothing ever renders a key.
export function translator(code) {
  const table = STRINGS[code]
  return (key, english) => (table && table[key]) || english
}

export function isTranslated(code) {
  return Boolean(STRINGS[code])
}
