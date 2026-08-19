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
  'nav.start_over': 'फिर से शुरू करें',
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

  'help.open': 'मदद',
  'help.title': 'मदद',
  'help.close': 'मदद बंद करें',
  'help.new_chat': 'नई बातचीत',
  'help.recentre': 'बीच में लाएँ',
  'help.thinking': 'देख रहे हैं',
  'help.placeholder': 'इस स्क्रीन के बारे में कुछ भी पूछें',
  'help.send': 'पूछें',
  'help.raise': 'यह टीम तक पहुँचाएँ',
  'help.ticket_title': 'टीम तक पहुँचाएँ',
  'help.ticket_subject': 'एक पंक्ति में',
  'help.ticket_detail': 'और कुछ बताना चाहें तो',
  'help.file': 'भेज दें',
  'help.filing': 'भेजा जा रहा है',
  'help.cancel': 'रहने दें',
  'help.footer':
    'सिर्फ़ मार्गदर्शन, कोई चिकित्सकीय सलाह नहीं, और यह आपके इलाज में कुछ भी नहीं बदल सकता। बंद करते ही यहाँ की बातचीत मिट जाती है।',
  'settings.tickets': 'आपके टिकट',
  'settings.tickets.none':
    'अभी कुछ नहीं भेजा गया। मदद वाली खिड़की से आप जो भेजेंगे, वह यहाँ अपने नंबर के साथ दिखेगा।',
  'settings.tickets.stage': 'मिल गया',
  'settings.tickets.note':
    'अभी इस पर कोई काम शुरू नहीं हुआ है, और यह कहना उस स्थिति से बेहतर है जो झूठा दिखावा करे',
  'settings.language': 'भाषा',
  'settings.language.hint':
    'यह ऐप की अपनी भाषा बदलता है। आपकी पॉलिसी से पढ़ी गई बातें उसी भाषा में रहती हैं जिसमें दस्तावेज़ है।',
  'settings.theme': 'दिखावट',
  'settings.text_size': 'अक्षरों का आकार',

  'nav.home': 'आपके इलाज',
  'nav.steps': '{count} चरण',
  'nav.text.normal': 'सामान्य अक्षर आकार पर लाएँ',
  'nav.text.larger': 'अक्षर बड़े करें',
  'nav.settings': 'सेटिंग',
  'nav.sections': 'भाग',

  'signin.placeholder': 'आपका नाम, या जो आपको याद रहे',

  'home.resume': 'जहाँ छोड़ा था वहीं से चलें, या नई भर्ती शुरू करें।',
  'home.first': 'पॉलिसी पढ़वाकर शुरू करें। उसके बाद का सब कुछ यहीं सहेजा जाता है।',
  'home.switch_user': 'आप नहीं?',
  'home.policy_read': 'पॉलिसी पढ़ी गई',
  'home.delete': '{stay} हटाएँ',
  'home.delete.short': 'हटाएँ',
  'home.stored_locally':
    'ये सिर्फ़ इसी डिवाइस पर रखे हैं। ब्राउज़र का डेटा साफ़ करने पर ये मिट जाते हैं।',

  'restore.opening':
    'आपका इलाज खोला जा रहा है। सर्वर को जागने में थोड़ा समय लग सकता है।',

  'reading.policy': 'आपकी पॉलिसी पढ़ी जा रही है',
  'reading.policy.waiting': 'आपकी फ़ाइलें भेजी जा रही हैं। यह पन्ना खुला रखें।',
  'reading.policy.hint':
    'लंबे दस्तावेज़ और फ़ोन से खींची तस्वीरें ज़्यादा समय लेती हैं। आप इसे पीछे खुला छोड़ सकते हैं।',
  'reading.search': 'आपके विकल्प खोजे जा रहे हैं',
  'reading.search.hint':
    'दायरे के हर अस्पताल का खर्च आपकी पॉलिसी के हिसाब से, एक-एक करके जोड़ा जा रहा है।',
  'reading.bill': 'आपका बिल पढ़ा जा रहा है',
  'reading.bill.waiting': 'बिल भेजा जा रहा है। यह पन्ना खुला रखें।',
  'reading.bill.hint':
    'तस्वीर में PDF से ज़्यादा समय लगता है, क्योंकि जाँचने से पहले हर पंक्ति पहचाननी पड़ती है।',

  'locked.policy': 'आपका कवर',
  'locked.policy.why':
    'पॉलिसी पढ़ ली जाने पर, आप किस-किस चीज़ के लिए कवर हैं, वह सब यहाँ दिखेगा, और जो हमने ग़लत पढ़ा हो उसे आप सुधार सकेंगे।',
  'locked.search': 'अस्पताल',
  'locked.search.why':
    'हम दायरे के हर अस्पताल का खर्च आपकी अपनी पॉलिसी के हिसाब से जोड़ते हैं, इसलिए पहले आपका कवर चाहिए।',

  'gone.title': 'यह इलाज इस डिवाइस पर नहीं है',
  'gone.why':
    'इलाज उसी डिवाइस पर सहेजे जाते हैं जहाँ वे शुरू हुए थे। अगर यह लिंक किसी दूसरे फ़ोन या दूसरे ब्राउज़र से आया है, तो वह भर्ती वहीं है, यहाँ नहीं।',
  'gone.home': 'आपके इलाज',
  'gone.new': 'नया इलाज शुरू करें',

  'rail.cover': 'आपका कवर',
  'rail.check': 'हमने क्या पढ़ा, देखें',
  'rail.room': 'जिस कमरे का कवर है',
  'rail.treatment': 'इलाज',
  'rail.cheapest': 'आपके लिए सबसे सस्ता',
  'rail.title': 'अब तक',
  'rail.change': 'बदलें',

  'activity.title': 'गतिविधि',
  'activity.subtitle': 'सिस्टम का हर कदम',
  'activity.live': 'चालू',
  'activity.idle': 'ठहरा हुआ',
  'activity.empty': 'पॉलिसी पढ़े जाने के साथ यहाँ कदम दिखने लगेंगे।',
  'activity.count': '{count} चरण',
  'activity.attention': '{count} पर ध्यान चाहिए',

  'time.now': 'अभी',
  'time.minutes': '{count} मिनट पहले',
  'time.hours': '{count} घंटे पहले',
  'time.yesterday': 'कल',
  'time.days': '{count} दिन पहले',

  'error.dismiss': 'हटाएँ',

  'upload.title': 'जानिए आपके अस्पताल के इलाज पर असल में कितना खर्च आएगा',
  'upload.subtitle':
    'अपनी स्वास्थ्य बीमा पॉलिसी अपलोड करें और हम बताएँगे कि किन अस्पतालों में आपका कवर है, कौन सा कमरा आपका हक़ है, और आपको खुद कितना देना पड़ेगा।',
  'upload.tab.file': 'मेरी पॉलिसी अपलोड करें',
  'upload.tab.manual': 'मेरे पास दस्तावेज़ नहीं है',
  'upload.insurer': 'आपका बीमा किसके साथ है?',
  'upload.insurer.hint':
    'इससे हमें पता चलता है कि किन अस्पतालों में आपको कैशलेस इलाज मिलेगा।',
  'upload.insurer.choose': 'अपनी बीमा कंपनी चुनें',
  'upload.insurer.companies': 'बीमा कंपनियाँ',
  'upload.insurer.schemes': 'सरकारी योजनाएँ',
  'upload.drop': 'अपनी पॉलिसी यहाँ छोड़ें, या चुनने के लिए दबाएँ',
  'upload.drop.more': 'और पन्ना जोड़ें, या चुनने के लिए दबाएँ',
  'upload.drop.hint':
    'PDF और तस्वीरें, दोनों चलती हैं, और आप कई जोड़ सकते हैं। फ़ोन से खींची हर पन्ने की तस्वीर भी ठीक है; हम उन्हें पढ़कर आपस में जोड़ लेंगे।',
  'upload.too_many':
    'यह {limit} फ़ाइलों से ज़्यादा है। जिन पन्नों पर आपका कवर लिखा है, आम तौर पर वे ही काफ़ी होते हैं।',
  'upload.too_large':
    'ये मिलाकर {size} MB हो जाते हैं, और हम {limit} MB तक पढ़ सकते हैं। जिन पन्नों पर आपका कवर लिखा है, आम तौर पर वे ही काफ़ी होते हैं।',
  'upload.remove': '{name} हटाएँ',
  'upload.reading': 'आपकी पॉलिसी पढ़ी जा रही है।',
  'upload.read': 'मेरी पॉलिसी पढ़ें',
  'upload.read_many': 'ये {count} दस्तावेज़ पढ़ें',
  'upload.done': 'आपकी पॉलिसी पढ़ ली गई',
  'upload.done.hint':
    'उसमें क्या लिखा है, वह नीचे है। आगे बढ़ने से पहले जो हमने ग़लत पढ़ा हो, उसे सुधार लें।',

  'manual.sum_insured': 'कुल कवर की रकम',
  'manual.sum_insured.hint':
    'आपकी बीमा कंपनी साल भर में ज़्यादा से ज़्यादा जितना देती है।',
  'manual.room': 'कमरे के किराए की सीमा',
  'manual.room.hint':
    'ज़्यादातर पॉलिसियों में इसकी सीमा होती है। सीमा से ऊपर का कमरा लेने पर बाकी खर्चों पर भी बीमा कंपनी कम देती है।',
  'manual.room.flat': 'रोज़ की तय रकम',
  'manual.room.pct': 'मेरे कवर का प्रतिशत',
  'manual.room.none': 'कोई सीमा नहीं',
  'manual.room.amount': 'रोज़ की रकम',
  'manual.room.percent': 'कवर का प्रतिशत, रोज़ के लिए',
  'manual.copay': 'आपका हिस्सा',
  'manual.copay.hint': 'हर दावे का जितना हिस्सा आप खुद देते हैं। न हो तो 0 लिखें।',
  'manual.working': 'चल रहा है…',
  'manual.continue': 'आगे बढ़ें',

  'treatment.placeholder': 'आपको जो बताया गया वह लिखें, जैसे स्टेंट, प्रसव, पित्ताशय',
  'treatment.no_match':
    'इससे कुछ नहीं मिला। कोई आसान शब्द आज़माएँ, जैसे शरीर का वह हिस्सा, या डॉक्टर की पर्ची पर लिखा शब्द।',

  'policy.warnings': 'आपके अपलोड किए दस्तावेज़ के बारे में',
  'policy.title': 'आपका कवर',
  'policy.sum_insured': 'इस साल का कुल कवर',
  'policy.sum_insured.hint': 'जैसे आपकी पॉलिसी में लिखा हो, जैसे 5 लाख या 500000',
  'policy.remaining': 'इस साल बचा कवर',
  'policy.remaining.hint': 'इस पॉलिसी वर्ष में पहले किए गए किसी दावे के बाद जो बचा है।',
  'policy.remaining.assumed':
    'हमने मान लिया है कि इस साल कोई दावा नहीं हुआ। अगर आप पहले दावा कर चुके हैं तो इसे सुधारें: इससे हर अनुमान बदल जाता है।',
  'policy.remaining.restore':
    'कवर खत्म हो जाए तो आपकी पॉलिसी उसे साल में एक बार वापस भर देती है।',
  'policy.room': 'जिस कमरे का कवर है',
  'policy.room.hint': 'रोज़ की रकम, 1% जैसा प्रतिशत, कमरे का दर्जा, या "कोई सीमा नहीं"',
  'policy.room.note':
    'महँगा कमरा लेने पर सर्जन, थिएटर और नर्सिंग के खर्च पर भी बीमा कंपनी कम देती है।',
  'policy.copay': 'हर दावे में आपका हिस्सा',
  'policy.copay.none': 'कुछ नहीं',
  'policy.copay.hint': 'प्रतिशत में, जैसे 10। न हो तो 0 लिखें।',
  'policy.copay.age':
    'सिर्फ़ {age} साल और उससे ऊपर के सदस्यों पर। इससे छोटे सदस्य के दावे पर कोई हिस्सा नहीं देना पड़ता।',
  'policy.icu': 'ICU का कवर',
  'policy.deductible': 'पहले आप देंगे',
  'policy.deductible.none': 'कुछ नहीं',
  'policy.deductible.hint':
    'यह सिर्फ़ टॉप-अप पॉलिसियों में होता है। आपकी में न हो तो 0 लिखें।',
  'policy.deductible.note': 'यह टॉप-अप पॉलिसी है। यह इस रकम से ऊपर ही देती है।',
  'policy.consumables': 'इस्तेमाल की सामग्री',
  'policy.covered': 'कवर है',
  'policy.not_covered': 'कवर नहीं है',
  'policy.consumables.note': 'दस्ताने, सिरिंज और ऐसी चीज़ें आपको खुद देनी होंगी।',
  'policy.daycare': 'एक दिन से कम का इलाज',
  'policy.not_stated': 'नहीं लिखा है',
  'policy.daycare.no':
    'कवर के लिए पूरे एक दिन की भर्ती चाहिए। मोतियाबिंद, डायलिसिस जैसे इलाजों का पैसा नहीं मिलेगा।',
  'policy.daycare.unknown':
    'आपके दस्तावेज़ में यह नहीं लिखा। पूछ लेना ठीक रहेगा, क्योंकि कवर के लिए आम तौर पर 24 घंटे की भर्ती चाहिए होती है।',
  'policy.sublimits': 'अलग सीमाएँ',
  'policy.continue': 'जिन अस्पतालों का कवर है, वे दिखाएँ',
  'policy.to_confirm': '{count} की पुष्टि बाकी',
  'policy.from_scan': 'स्कैन से पढ़ा गया',
  'policy.read_cleanly': 'साफ़-साफ़ पढ़ा गया',

  'scheme.cover': 'इस साल का कवर',
  'scheme.cover.note': 'साल भर के लिए, पूरे परिवार में मिलाकर।',
  'scheme.you_pay': 'सूचीबद्ध अस्पताल में आप क्या देंगे',
  'scheme.you_pay.value': 'कुछ नहीं',
  'scheme.you_pay.note':
    'इलाज एक तय पैकेज दर पर लिया जाता है। न कोई बिल चुकाना है, न कोई दावा करना है।',
  'scheme.room': 'जो कमरा शामिल है',
  'scheme.room.note':
    'इससे ऊँचा कमरा लेना आपके अपने खर्च पर है, पर इससे बाकी किसी चीज़ का कवर कम नहीं होता।',
  'scheme.consumables': 'सामग्री, इम्प्लांट, दवाइयाँ, जाँच',
  'scheme.consumables.value': 'पैकेज में शामिल',
  'scheme.empanelled_only':
    'यह सिर्फ़ {scheme} के लिए सूचीबद्ध अस्पताल में ही चलता है। कहीं और यह योजना कुछ नहीं देती, और बाद में कोई दावा भी नहीं होता। हम आपको जो अस्पताल दिखाते हैं, वे इसी आधार पर छाँटे गए हैं।',

  'second.title': 'आपकी दूसरी पॉलिसी',
  'second.remove': 'हटाएँ',
  'second.cover': 'कवर',
  'second.room': 'कमरा',
  'second.above': 'इससे ऊपर ही देती है',
  'second.topup.how':
    'टॉप-अप वह देता है जो ऊपर वाली सीमा तक का कवर हो जाने के बाद बचता है। हम पहले आपकी पहली पॉलिसी लगाते हैं, फिर बाकी रकम पर यह।',
  'second.how':
    'हम एक पॉलिसी लगाते हैं, फिर बची रकम दूसरी पर डालते हैं, और बताते हैं कि किस क्रम में आपका खर्च कम पड़ता है।',
  'second.add': '+ मेरे पास एक और पॉलिसी है',
  'second.add.why':
    'नौकरी वाली कवर, या टॉप-अप। दूसरी पॉलिसी वह देती है जो पहली छोड़ देती है, और ज़्यादातर लोग उससे दावा करते ही नहीं।',
  'second.other': 'आपकी दूसरी पॉलिसी',
  'second.cancel': 'रहने दें',
  'second.form.insurer': 'यह किसके साथ है?',
  'second.form.insurer.hint': 'बीमा कंपनी का नाम, या आपके दफ़्तर का।',
  'second.form.insurer.placeholder': 'जैसे मेरे दफ़्तर की ग्रुप पॉलिसी',
  'second.form.cover': 'कितना कवर?',
  'second.form.room': 'कमरे के किराए की सीमा',
  'second.form.room.none': 'कोई सीमा नहीं',
  'second.form.room.flat': 'रोज़ की तय रकम',
  'second.form.room.amount': 'रोज़ की रकम',
  'second.form.deductible': 'क्या यह एक रकम से ऊपर ही देती है?',
  'second.form.deductible.hint':
    'टॉप-अप पॉलिसियाँ ऐसा करती हैं। आपकी न करती हो तो 0 ही रहने दें।',
  'second.form.adding': 'जोड़ा जा रहा है…',
  'second.form.submit': 'यह पॉलिसी जोड़ें',

  'insured.title': 'किन-किन का कवर है',
  'insured.period': '{from} से {to} तक का कवर',
  'insured.period.open': '{from} से कवर',
  'insured.ending':
    'यह पॉलिसी वर्ष {days} दिन में खत्म हो रहा है। नवीनीकरण पर आपका कवर फिर से शुरू होता है, इसलिए उस तारीख़ के इधर-उधर की भर्ती अलग-अलग साल के कवर पर जाती है।',
  'insured.ended':
    'यह पॉलिसी वर्ष खत्म हो चुका है। इन आँकड़ों पर भरोसा करने से पहले देख लें कि नवीनीकरण हुआ था या नहीं।',

  'waiting.title': 'प्रतीक्षा अवधि',
  'waiting.served': 'पूरी हो चुकी। {date} से कवर है।',
  'waiting.from': '{date} से कवर।',
  'waiting.no_start':
    'यह पॉलिसी कब शुरू हुई, यह हम नहीं पढ़ पाए, इसलिए यह नहीं बता सकते कि ये अब भी लागू हैं या नहीं। इलाज चुनने पर आपसे पूछा जाएगा।',
  'waiting.pending':
    'दिखाई गई तारीख़ से पहले किया गया दावा नामंज़ूर हो जाएगा। आप जो इलाज चुनेंगे, उसके हिसाब से हम यह जाँचते हैं।',

  'fact.correct.label': '{field} सुधारें',
  'fact.correct': 'इसे सुधारें',
  'fact.saving': 'सहेजा जा रहा है…',
  'fact.save': 'सहेजें',
  'fact.cancel': 'रहने दें',

  'ask.placeholder.percent': 'जैसे 10%, या दस प्रतिशत',
  'ask.placeholder.amount': 'जैसे 5 लाख, 5,00,000, या कोई सीमा नहीं',
  'ask.confirming': 'बस पक्का कर लें',
  'ask.title': 'आपसे एक बात जाननी है',
  'ask.remaining': 'इसके बाद {count} और',
  'ask.page': 'हम आपके दस्तावेज़ के पन्ना {page} को देख रहे थे।',
  'ask.source.page': '{source} से, पन्ना {page}',
  'ask.source': '{source} से',
  'ask.other': 'इनमें से कोई नहीं, मैं बताता हूँ',
  'ask.reading': 'पढ़ा जा रहा है…',
  'ask.confirm': 'पक्का करें',
  'ask.free_text':
    'जैसा आपके दस्तावेज़ में लिखा है वैसा ही लिखें, शब्दों में या अंकों में। इस्तेमाल करने से पहले हम इसे आपको पढ़कर दिखाएँगे।',
  'ask.skip': 'यह मुझे नहीं पता',
  'ask.skip.hint': 'हम आगे बढ़ेंगे और जहाँ पक्का न हो, वहाँ बता देंगे।',

  'evidence.title': 'ये आँकड़े कहाँ से आए',
  'evidence.count': 'आपके दस्तावेज़ से पढ़े गए {count} अंश',
  'evidence.hide': 'छिपाएँ',
  'evidence.show': 'देखें',
  'evidence.page': 'पन्ना {page}',
  'evidence.uncertain': 'पक्का नहीं',

  'search.title': 'आपको कौन सा इलाज चाहिए?',
  'search.subtitle':
    'हम वे अस्पताल ढूँढेंगे जो यह करते हैं, और बताएँगे कि हर एक में आपको कितना देना पड़ेगा।',
  'search.treatment': 'इलाज',
  'search.treatment.hint':
    'आपको जो बताया गया है वही लिखें। हम उसे सबसे मिलते-जुलते इलाज से जोड़ लेंगे, जिसका खर्च हम निकाल सकते हैं।',
  'search.patient': 'किसका इलाज होना है?',
  'search.patient.hint':
    'आपकी पॉलिसी सिर्फ़ बड़ी उम्र के सदस्यों पर हिस्सा लेती है, इसलिए इससे आँकड़े बदल जाते हैं।',
  'search.patient.unsure': 'अभी पक्का नहीं',
  'search.city': 'शहर',
  'search.city.count': '{city} ({count} अस्पताल)',
  'search.distance': 'आप कितनी दूर तक जा सकते हैं?',
  'search.distance.upto': '{km} किमी तक',
  'search.preference': 'आपके लिए सबसे ज़रूरी क्या है?',
  'search.urgency': 'कब तक?',
  'search.urgency.planned': 'पहले से तय',
  'search.urgency.urgent': 'कुछ ही दिनों में',
  'search.urgency.emergency': 'आपात स्थिति',
  'search.searching': 'खोजा जा रहा है…',
  'search.go': 'मेरे विकल्प दिखाएँ',

  'preference.protect_money': 'मेरा खर्च कम रहे',
  'preference.best_care': 'सबसे अच्छी सुविधा वाला अस्पताल',
  'preference.nearest': 'सबसे जल्दी पहुँचूँ',
  'preference.balanced': 'संतुलित',

  'eligibility.declined': 'आपकी बीमा कंपनी यह दावा नामंज़ूर कर देगी',
  'eligibility.declined.hint': 'नीचे दिए खर्च वे हैं जो आपको खुद देने होंगे।',
  'eligibility.one_answer': 'एक जवाब से यह तय हो जाएगा।',
  'eligibility.why_ask':
    'किसी पॉलिसी में यह लिखा नहीं है, और इससे जवाब बदल जाता है, इसलिए हमें पूछना पड़ रहा है। आपका जवाब इसी डिवाइस पर रहता है।',
  'eligibility.had_before': 'हाँ, यह पहले से था',
  'eligibility.came_after': 'नहीं, यह बाद में हुआ',
  'eligibility.accident': 'यह दुर्घटना थी',

  'results.looked_at.city': 'हमने {city} के {count} अस्पताल देखे।',
  'results.looked_at': 'हमने {count} अस्पताल देखे।',
  'results.relaxed': 'ये मिलने के लिए हमें आपकी शर्तें कुछ ढीली करनी पड़ीं',
  'results.excluded': 'बाकी अस्पताल क्यों छूट गए',
  'results.filter': 'नाम या इलाके से अस्पताल ढूँढें',
  'results.filter.label': 'इन नतीजों को अस्पताल के नाम या इलाके से छाँटें',
  'results.filter.none': '"{query}" से यहाँ कोई अस्पताल नहीं मिला।',
  'results.filter.some': '{total} में से {shown} "{query}" से मिलते हैं।',
  'results.strong': 'अच्छा विकल्प',
  'results.travel': 'लगभग {minutes} मिनट',
  'results.you_would_pay': 'आप देंगे',
  'results.up_to': 'अधिकतम',
  'results.up_to.driver': '{driver} होने पर',
  'results.hospital_bill': 'अस्पताल का बिल',
  'results.insurer_pays_short': 'बीमा कंपनी देगी',
  'results.upfront': 'पहले आपको देना होगा',
  'results.settlement': 'भुगतान का तरीक़ा',
  'results.room': 'कमरा',
  'results.room.rate': '{room}, {rate} रोज़',
  'results.hide_breakdown': 'ब्योरा छिपाएँ',
  'results.show_breakdown': 'मेरा पैसा कहाँ जाता है?',
  'results.track': 'मेरा इलाज यहीं देखें',

  'exclusion.too_far': 'आपकी दूरी की सीमा से बाहर',
  'exclusion.procedure_unavailable': 'यह इलाज नहीं करते',
  'exclusion.specialty_unavailable': 'यह विभाग नहीं है',
  'exclusion.not_cashless': 'आपके कैशलेस नेटवर्क में नहीं',
  'exclusion.no_bed_available': 'अभी कोई बिस्तर खाली नहीं',
  'exclusion.no_eligible_room': 'आपके दर्जे का कमरा नहीं',
  'exclusion.scheme_not_empanelled': 'आपकी योजना के लिए सूचीबद्ध नहीं',

  'room.general_ward': 'जनरल वार्ड',
  'room.twin_sharing': 'दो लोगों वाला कमरा',
  'room.single_private': 'अकेले का कमरा',
  'room.deluxe': 'डीलक्स कमरा',
  'room.suite': 'सुइट',
  'room.icu': 'ICU',

  'settlement.cashless': 'कैशलेस',
  'settlement.reimbursement': 'पहले खुद दें, बाद में दावा करें',
  'settlement.scheme_package': 'योजना का पैकेज',

  'waterfall.title': 'अस्पताल के बिल से आपके खर्च तक',
  'waterfall.lines': 'अस्पताल का बिल, एक-एक चीज़',

  'journey.title': 'आपका इलाज',
  'journey.per_day': '₹{amount} रोज़',
  'journey.preauth.file': 'पूर्व-मंज़ूरी भेज दी गई, ऐसा दर्ज करें',
  'journey.timeline.skipped': '{stages} छोड़े गए।',
  'journey.charges.count': '{count} दर्ज, कुल {total}',
  'journey.charge.options': '{head} के विकल्प',
  'journey.charge.close_menu': 'मेनू बंद करें',
  'journey.charge.edit': 'बदलें',
  'journey.charge.delete': 'हटाएँ',
  'journey.charge.head': 'यह किस चीज़ का है?',
  'journey.charge.amount': 'रकम',
  'journey.charge.when': 'कब',
  'journey.charge.save': 'सहेजें',
  'journey.charge.cancel': 'बंद करें',
  'journey.charge.new_day': 'यह इलाज का नया दिन है',
  'journey.charge.add': 'खर्च जोड़ें',
  'journey.add_charge.hint':
    'बिल जैसे-जैसे आएँ, दर्ज करते जाएँ, ताकि अनुमान सही बना रहे।',
  'journey.receipt.too_large':
    'यह फ़ाइल {size} MB की है। हम ज़्यादा से ज़्यादा {limit} MB ले सकते हैं।',
  'journey.receipt.remove': 'हटाएँ',
  'journey.receipt.attach': 'बिल या रसीद लगाएँ (ज़रूरी नहीं)',
  'journey.checklist.count': '{total} में से {done}',
  'journey.checklist.now': 'अभी',
  'journey.position.you_pay': 'अब तक आप देंगे',
  'journey.position.split':
    'अस्पताल ने {billed} का बिल बनाया है। उसमें से {covered} आपकी बीमा कंपनी देगी।',
  'journey.position.hide': 'फ़र्क कहाँ से आता है, छिपाएँ',
  'journey.position.show': 'फ़र्क कहाँ से आता है, देखें',
  'journey.burn.used': 'अब तक इस्तेमाल हुआ कवर',
  'journey.burn.of': '{total} में से {used}',
  'journey.burn.left': '{amount} बचा',
  'journey.burn.rate': '{amount} रोज़',
  'journey.burn.reached': 'कवर आज ही पूरा हो गया',
  'journey.burn.days_left': 'लगभग {days} दिन का कवर बचा है',
  'journey.advance.settled': 'आपका दावा निपट गया',
  'journey.advance.title': 'अभी आप कहाँ हैं?',
  'journey.advance.settled.hint': 'कुछ बदले तो आप अब भी पिछले चरण पर लौट सकते हैं।',
  'journey.advance.hint':
    'जैसे-जैसे बात आगे बढ़े, इसे बदलते रहें। आप कभी भी पीछे जा सकते हैं।',
  'journey.advance.stage': 'चरण',
  'journey.advance.here': 'आप यहाँ हैं',
  'journey.advance.back': 'पीछे जाएँ',
  'journey.advance.back.hint':
    'इससे आपका इलाज {stage} पर लौट जाएगा। आपका दर्ज किया कुछ भी नहीं मिटेगा।',
  'journey.advance.go_back': 'इस चरण पर लौटें',
  'journey.advance.update': 'बदलें',
  'journey.skip.cancel': 'रहने दें',
  'journey.skip.title': 'बस बता दें',
  'journey.skip.body': 'सीधे {stage} पर जाने से {skipped} छूट जाते हैं।',
  'journey.skip.reassure':
    'यह अक्सर बिलकुल ठीक होता है। बहुत सी भर्तियों में इनमें से कुछ आते ही नहीं। आपका अनुमान दोनों हाल में सही रहता है, और आप बाद में किसी भी चरण पर लौट सकते हैं।',
  'journey.skip.note': 'कारण लिखना चाहूँगा (ज़रूरी नहीं)',
  'journey.skip.placeholder':
    'जैसे: आपात स्थिति में भर्ती हुए, इसलिए पूर्व-मंज़ूरी का समय नहीं मिला।',
  'journey.skip.confirm': '{stage} पर जाएँ',
  'journey.skip.decline': 'अभी नहीं',

  'head.room_rent': 'कमरे का किराया',
  'head.icu_charges': 'ICU का खर्च',
  'head.investigations': 'जाँच और स्कैन',
  'head.pharmacy': 'दवाइयाँ',
  'head.consumables': 'इस्तेमाल की सामग्री',
  'head.surgeon_fee': 'सर्जन की फ़ीस',
  'head.ot_charges': 'ऑपरेशन थिएटर',
  'head.nursing': 'नर्सिंग',
  'head.implants': 'इम्प्लांट',
  'head.non_medical': 'ग़ैर-चिकित्सा सामान',

  'list.a_stage': 'एक चरण',
  'list.and': 'और',

  'bill.what_we_do':
    'एक-एक चीज़ वाला बिल माँगें, एक पंक्ति वाला कुल नहीं, और उसकी तस्वीर लें। हम उसे पंक्ति-दर-पंक्ति पढ़कर बताते हैं कि दस्तख़त करने से पहले क्या पूछने लायक है: वे चीज़ें जो नियामक के हिसाब से पहले ही किसी और खर्च में शामिल हैं, दो बार लिखी पंक्तियाँ, वे आँकड़े जो गुणा करने पर नहीं मिलते, और वह कटौती जो आपकी बीमा कंपनी करेगी पर बिलिंग काउंटर नहीं बताएगा।',
  'bill.photo_hint':
    'सामने से, अच्छी रोशनी में। बिलिंग काउंटर से मिला PDF बिलकुल सही पढ़ा जाता है।',
  'bill.settles_to.hint': 'वही गणना जो अनुमान में थी, असली बिल पर लगाई गई।',
  'bill.col.line': 'क्रम',
  'bill.col.item': 'चीज़',
  'bill.col.head': 'मद',
  'bill.col.amount': 'रकम',

  'settings.close': 'सेटिंग बंद करें',
  'settings.close.short': 'बंद करें',
  'settings.theme.label': 'रंग-रूप',
  'settings.theme.hint': '"सिस्टम" आपके फ़ोन या कंप्यूटर के हिसाब से चलता है।',
  'settings.theme.light': 'उजला',
  'settings.theme.dark': 'गहरा',
  'settings.theme.system': 'सिस्टम',
  'settings.text_size.hint':
    'पूरे ऐप में बड़े अक्षर, ताकि जल्दी में फ़ोन पर पढ़ा जा सके।',
  'settings.text_size.default': 'सामान्य',
  'settings.text_size.large': 'बड़ा',
  'settings.session': 'यह सत्र',
  'settings.session.hint':
    'आपकी पॉलिसी और आपके लिए मिले अस्पताल सिर्फ़ तब तक रखे जाते हैं जब तक यह टैब खुला है। पन्ना दोबारा लोड करने पर सब शुरू से होता है।',
  'settings.clear.yes': 'हाँ, मिटा दें',
  'settings.clear.no': 'रहने दें',
  'settings.clear': 'मिटाकर शुरू से करें',
  'settings.developer': 'डेवलपर',
  'settings.developer.note': 'जाँच के लिए। यहाँ की किसी चीज़ से ऐप की गणना नहीं बदलती।',
  'settings.activity': 'गतिविधि पैनल दिखाएँ',
  'settings.activity.hint':
    'हर पाइपलाइन कदम की सीधी झलक, समय के साथ। वही घटनाएँ जो सर्वर अपने लॉग में लिखता है।',
  'settings.api': 'API',
  'settings.api.reachable': 'पहुँच में है',
  'settings.api.unreachable': 'पहुँच में नहीं',
  'settings.reset': 'सेटिंग शुरुआती हाल में लाएँ',

  disclaimer:
    'ये अनुमान केवल मार्गदर्शन के लिए हैं। यह कोई कोटेशन, मंज़ूरी या चिकित्सकीय सलाह नहीं है। सभी रकमें अपनी बीमा कंपनी और अस्पताल के बीमा काउंटर से जाँच लें।',
}

const kn = {
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

const mr = {
  'nav.start_over': 'पुन्हा सुरू करा',
  'help.open': 'मदत',
  'help.title': 'मदत',
  'help.close': 'मदत बंद करा',
  'help.new_chat': 'नवीन संवाद',
  'help.recentre': 'मध्यभागी आणा',
  'help.thinking': 'पाहत आहोत',
  'help.placeholder': 'या स्क्रीनविषयी काहीही विचारा',
  'help.send': 'विचारा',
  'help.raise': 'हे टीमपर्यंत पोहोचवा',
  'help.ticket_title': 'टीमपर्यंत पोहोचवा',
  'help.ticket_subject': 'एका ओळीत',
  'help.ticket_detail': 'आणखी काही सांगायचे असल्यास',
  'help.file': 'पाठवा',
  'help.filing': 'पाठवत आहोत',
  'help.cancel': 'नको',
  'help.footer':
    'हे फक्त मार्गदर्शन आहे, वैद्यकीय सल्ला नाही, आणि ते तुमच्या उपचारात काहीही बदलू शकत नाही. बंद करताच इथला संवाद पुसला जातो.',
  'settings.tickets': 'तुमची तिकिटे',
  'settings.tickets.none':
    'अजून काहीही पाठवलेले नाही. मदत खिडकीतून तुम्ही जे पाठवाल ते इथे त्याच्या क्रमांकासह दिसेल.',
  'settings.tickets.stage': 'मिळाले',
  'settings.tickets.note':
    'यावर अजून कोणतेही काम सुरू झालेले नाही, आणि खोटा आभास देणाऱ्या स्थितीपेक्षा हे सांगणे बरे',
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

  'nav.home': 'तुमचे उपचार',
  'nav.steps': '{count} पायऱ्या',
  'nav.text.normal': 'सामान्य अक्षर आकारावर आणा',
  'nav.text.larger': 'अक्षरे मोठी करा',
  'nav.settings': 'सेटिंग',
  'nav.sections': 'भाग',

  'signin.placeholder': 'तुमचे नाव, किंवा तुम्हाला लक्षात राहील असे काहीही',

  'home.resume': 'जिथे थांबला होतात तिथून पुढे जा, किंवा नवीन भरती सुरू करा.',
  'home.first': 'पॉलिसी वाचून घेऊन सुरुवात करा. त्यानंतरचे सर्व इथेच जतन होते.',
  'home.switch_user': 'तुम्ही नाही?',
  'home.policy_read': 'पॉलिसी वाचली',
  'home.delete': '{stay} काढून टाका',
  'home.delete.short': 'काढा',
  'home.stored_locally':
    'हे फक्त याच डिव्हाइसवर ठेवलेले आहेत. ब्राउझरचा डेटा पुसल्यास हे नाहीसे होतात.',

  'restore.opening':
    'तुमचा उपचार उघडला जात आहे. सर्व्हरला जागे व्हायला थोडा वेळ लागू शकतो.',

  'reading.policy': 'तुमची पॉलिसी वाचली जात आहे',
  'reading.policy.waiting': 'तुमच्या फाइल्स पाठवल्या जात आहेत. हे पान उघडे ठेवा.',
  'reading.policy.hint':
    'लांब कागदपत्रे आणि फोनवरील फोटो जास्त वेळ घेतात. तुम्ही हे मागे उघडे ठेवू शकता.',
  'reading.search': 'तुमचे पर्याय शोधले जात आहेत',
  'reading.search.hint':
    'परिसरातील प्रत्येक रुग्णालयाचा खर्च तुमच्या पॉलिसीनुसार एक-एक करून काढला जात आहे.',
  'reading.bill': 'तुमचे बिल वाचले जात आहे',
  'reading.bill.waiting': 'बिल पाठवले जात आहे. हे पान उघडे ठेवा.',
  'reading.bill.hint':
    'फोटोला PDF पेक्षा जास्त वेळ लागतो, कारण तपासण्याआधी प्रत्येक ओळ ओळखावी लागते.',

  'locked.policy': 'तुमचे कवर',
  'locked.policy.why':
    'पॉलिसी वाचल्यावर, तुम्हाला कशाकशाचे कवर आहे ते सर्व इथे दिसेल, आणि आम्ही चुकीचे वाचले असल्यास तुम्ही ते दुरुस्त करू शकाल.',
  'locked.search': 'रुग्णालये',
  'locked.search.why':
    'आम्ही परिसरातील प्रत्येक रुग्णालयाचा खर्च तुमच्याच पॉलिसीनुसार काढतो, त्यामुळे आधी तुमचे कवर हवे.',

  'gone.title': 'हा उपचार या डिव्हाइसवर नाही',
  'gone.why':
    'उपचार ज्या डिव्हाइसवर सुरू झाले तिथेच जतन होतात. हा दुवा दुसऱ्या फोनवरून किंवा दुसऱ्या ब्राउझरवरून आला असेल, तर ती भरती तिथेच आहे, इथे नाही.',
  'gone.home': 'तुमचे उपचार',
  'gone.new': 'नवीन उपचार सुरू करा',

  'rail.cover': 'तुमचे कवर',
  'rail.check': 'आम्ही काय वाचले ते पाहा',
  'rail.room': 'ज्या खोलीचे कवर आहे',
  'rail.treatment': 'उपचार',
  'rail.cheapest': 'तुमच्यासाठी सर्वात स्वस्त',
  'rail.title': 'आतापर्यंत',
  'rail.change': 'बदला',

  'activity.title': 'हालचाल',
  'activity.subtitle': 'सिस्टमचे प्रत्येक पाऊल',
  'activity.live': 'चालू',
  'activity.idle': 'थांबलेले',
  'activity.empty': 'पॉलिसी वाचली जात असताना इथे पावले दिसू लागतील.',
  'activity.count': '{count} पायऱ्या',
  'activity.attention': '{count} कडे लक्ष हवे',

  'time.now': 'आत्ताच',
  'time.minutes': '{count} मिनिटांपूर्वी',
  'time.hours': '{count} तासांपूर्वी',
  'time.yesterday': 'काल',
  'time.days': '{count} दिवसांपूर्वी',

  'error.dismiss': 'बंद करा',

  'upload.title': 'तुमच्या रुग्णालयातील उपचारावर खरोखर किती खर्च येईल ते जाणून घ्या',
  'upload.subtitle':
    'तुमची आरोग्य विमा पॉलिसी अपलोड करा आणि कोणत्या रुग्णालयांत तुमचे कवर आहे, कोणती खोली तुमचा हक्क आहे, आणि तुम्हाला स्वतः किती द्यावे लागेल ते आम्ही सांगू.',
  'upload.tab.file': 'माझी पॉलिसी अपलोड करा',
  'upload.tab.manual': 'माझ्याकडे कागदपत्र नाही',
  'upload.insurer': 'तुमचा विमा कोणासोबत आहे?',
  'upload.insurer.hint':
    'यावरून कोणत्या रुग्णालयांत तुम्हाला कॅशलेस उपचार मिळेल ते आम्हाला कळते.',
  'upload.insurer.choose': 'तुमची विमा कंपनी निवडा',
  'upload.insurer.companies': 'विमा कंपन्या',
  'upload.insurer.schemes': 'सरकारी योजना',
  'upload.drop': 'तुमची पॉलिसी इथे टाका, किंवा निवडण्यासाठी दाबा',
  'upload.drop.more': 'आणखी पान जोडा, किंवा निवडण्यासाठी दाबा',
  'upload.drop.hint':
    'PDF आणि फोटो, दोन्ही चालतात, आणि तुम्ही अनेक जोडू शकता. फोनवर काढलेला प्रत्येक पानाचा फोटोही चालतो; आम्ही ते वाचून एकत्र जोडू.',
  'upload.too_many':
    'हे {limit} फाइलींपेक्षा जास्त आहे. तुमचे कवर लिहिलेली पानेच सहसा पुरेशी असतात.',
  'upload.too_large':
    'ही मिळून {size} MB होतात, आणि आम्ही {limit} MB पर्यंत वाचू शकतो. तुमचे कवर लिहिलेली पानेच सहसा पुरेशी असतात.',
  'upload.remove': '{name} काढा',
  'upload.reading': 'तुमची पॉलिसी वाचली जात आहे.',
  'upload.read': 'माझी पॉलिसी वाचा',
  'upload.read_many': 'ही {count} कागदपत्रे वाचा',
  'upload.done': 'तुमची पॉलिसी वाचली गेली',
  'upload.done.hint':
    'त्यात काय लिहिले आहे ते खाली आहे. पुढे जाण्याआधी आम्ही चुकीचे वाचले असल्यास ते दुरुस्त करा.',

  'manual.sum_insured': 'एकूण कवरची रक्कम',
  'manual.sum_insured.hint': 'तुमची विमा कंपनी वर्षभरात जास्तीत जास्त जितके देते.',
  'manual.room': 'खोली भाड्याची मर्यादा',
  'manual.room.hint':
    'बहुतेक पॉलिसींमध्ये याला मर्यादा असते. मर्यादेच्या वरची खोली घेतल्यास बाकी खर्चांवरही विमा कंपनी कमी देते.',
  'manual.room.flat': 'रोजची ठरलेली रक्कम',
  'manual.room.pct': 'माझ्या कवरची टक्केवारी',
  'manual.room.none': 'मर्यादा नाही',
  'manual.room.amount': 'रोजची रक्कम',
  'manual.room.percent': 'कवरची टक्केवारी, रोजसाठी',
  'manual.copay': 'तुमचा वाटा',
  'manual.copay.hint':
    'प्रत्येक दाव्याचा जितका वाटा तुम्ही स्वतः देता. नसेल तर 0 लिहा.',
  'manual.working': 'सुरू आहे…',
  'manual.continue': 'पुढे जा',

  'treatment.placeholder':
    'तुम्हाला जे सांगितले ते लिहा, उदा स्टेंट, प्रसूती, पित्ताशय',
  'treatment.no_match':
    'याने काहीही सापडले नाही. सोपा शब्द वापरून पाहा, उदा शरीराचा तो भाग, किंवा डॉक्टरांच्या चिठ्ठीवरील शब्द.',

  'policy.warnings': 'तुम्ही अपलोड केलेल्या कागदपत्राबद्दल',
  'policy.title': 'तुमचे कवर',
  'policy.sum_insured': 'या वर्षाचे एकूण कवर',
  'policy.sum_insured.hint':
    'तुमच्या पॉलिसीत जसे लिहिले असेल तसे, उदा 5 लाख किंवा 500000',
  'policy.remaining': 'या वर्षी शिल्लक कवर',
  'policy.remaining.hint': 'या पॉलिसी वर्षात आधी केलेल्या दाव्यानंतर जे शिल्लक आहे.',
  'policy.remaining.assumed':
    'या वर्षी कोणताही दावा झाला नाही असे आम्ही गृहीत धरले आहे. तुम्ही आधीच दावा केला असल्यास हे दुरुस्त करा: यामुळे प्रत्येक अंदाज बदलतो.',
  'policy.remaining.restore':
    'कवर संपले तर तुमची पॉलिसी ते वर्षातून एकदा पुन्हा भरून देते.',
  'policy.room': 'ज्या खोलीचे कवर आहे',
  'policy.room.hint':
    'रोजची रक्कम, 1% सारखी टक्केवारी, खोलीचा दर्जा, किंवा "मर्यादा नाही"',
  'policy.room.note':
    'महाग खोली घेतल्यास सर्जन, थिएटर आणि नर्सिंगच्या खर्चावरही विमा कंपनी कमी देते.',
  'policy.copay': 'प्रत्येक दाव्यातील तुमचा वाटा',
  'policy.copay.none': 'काहीही नाही',
  'policy.copay.hint': 'टक्केवारीत, उदा 10. नसेल तर 0 लिहा.',
  'policy.copay.age':
    'फक्त {age} वर्षे आणि त्यावरील सदस्यांवर. त्यापेक्षा लहान सदस्याच्या दाव्यावर कोणताही वाटा नाही.',
  'policy.icu': 'ICU चे कवर',
  'policy.deductible': 'आधी तुम्ही द्याल',
  'policy.deductible.none': 'काहीही नाही',
  'policy.deductible.hint':
    'हे फक्त टॉप-अप पॉलिसींमध्ये असते. तुमच्यात नसेल तर 0 लिहा.',
  'policy.deductible.note': 'ही टॉप-अप पॉलिसी आहे. ती या रकमेच्या वरचेच देते.',
  'policy.consumables': 'वापरण्याचे साहित्य',
  'policy.covered': 'कवर आहे',
  'policy.not_covered': 'कवर नाही',
  'policy.consumables.note':
    'हातमोजे, सिरिंज आणि तत्सम गोष्टी तुम्हालाच द्याव्या लागतील.',
  'policy.daycare': 'एका दिवसापेक्षा कमी उपचार',
  'policy.not_stated': 'लिहिलेले नाही',
  'policy.daycare.no':
    'कवरसाठी पूर्ण एका दिवसाची भरती लागते. मोतीबिंदू, डायलिसिस असे उपचार दिले जाणार नाहीत.',
  'policy.daycare.unknown':
    'तुमच्या कागदपत्रात हे लिहिलेले नाही. विचारून घेणे बरे, कारण कवरसाठी सहसा 24 तासांची भरती लागते.',
  'policy.sublimits': 'वेगळ्या मर्यादा',
  'policy.continue': 'ज्या रुग्णालयांचे कवर आहे ती दाखवा',
  'policy.to_confirm': '{count} ची खात्री बाकी',
  'policy.from_scan': 'स्कॅनमधून वाचले',
  'policy.read_cleanly': 'स्पष्टपणे वाचले',

  'scheme.cover': 'या वर्षाचे कवर',
  'scheme.cover.note': 'वर्षभरासाठी, संपूर्ण कुटुंबात मिळून.',
  'scheme.you_pay': 'सूचीबद्ध रुग्णालयात तुम्ही किती द्याल',
  'scheme.you_pay.value': 'काहीही नाही',
  'scheme.you_pay.note':
    'उपचार ठरलेल्या पॅकेज दरात घेतला जातो. ना बिल भरायचे, ना दावा करायचा.',
  'scheme.room': 'समाविष्ट असलेली खोली',
  'scheme.room.note':
    'यापेक्षा वरची खोली घेणे तुमच्या स्वतःच्या खर्चाने, पण त्यामुळे बाकी कशाचेही कवर कमी होत नाही.',
  'scheme.consumables': 'साहित्य, इम्प्लांट, औषधे, तपासण्या',
  'scheme.consumables.value': 'पॅकेजमध्ये समाविष्ट',
  'scheme.empanelled_only':
    'हे फक्त {scheme} साठी सूचीबद्ध रुग्णालयातच चालते. इतरत्र ही योजना काहीही देत नाही, आणि नंतर दावाही करता येत नाही. आम्ही दाखवत असलेली रुग्णालये याच आधारावर निवडली आहेत.',

  'second.title': 'तुमची दुसरी पॉलिसी',
  'second.remove': 'काढा',
  'second.cover': 'कवर',
  'second.room': 'खोली',
  'second.above': 'याच्या वरचेच देते',
  'second.topup.how':
    'टॉप-अप वरच्या मर्यादेपर्यंतचे कवर झाल्यावर उरलेले देते. आम्ही आधी तुमची पहिली पॉलिसी लावतो, मग उरलेल्या रकमेवर ही.',
  'second.how':
    'आम्ही एक पॉलिसी लावतो, मग उरलेली रक्कम दुसरीवर टाकतो, आणि कोणत्या क्रमाने तुमचा खर्च कमी होतो ते सांगतो.',
  'second.add': '+ माझ्याकडे आणखी एक पॉलिसी आहे',
  'second.add.why':
    'नोकरीचे कवर, किंवा टॉप-अप. दुसरी पॉलिसी पहिली जे सोडते ते देते, आणि बहुतेक लोक तिच्यातून दावाच करत नाहीत.',
  'second.other': 'तुमची दुसरी पॉलिसी',
  'second.cancel': 'राहू द्या',
  'second.form.insurer': 'ही कोणासोबत आहे?',
  'second.form.insurer.hint': 'विमा कंपनीचे नाव, किंवा तुमच्या कार्यालयाचे.',
  'second.form.insurer.placeholder': 'उदा माझ्या कार्यालयाची ग्रुप पॉलिसी',
  'second.form.cover': 'किती कवर?',
  'second.form.room': 'खोली भाड्याची मर्यादा',
  'second.form.room.none': 'मर्यादा नाही',
  'second.form.room.flat': 'रोजची ठरलेली रक्कम',
  'second.form.room.amount': 'रोजची रक्कम',
  'second.form.deductible': 'ही एका रकमेच्या वरचेच देते का?',
  'second.form.deductible.hint':
    'टॉप-अप पॉलिसी असे करतात. तुमची करत नसेल तर 0 च राहू द्या.',
  'second.form.adding': 'जोडले जात आहे…',
  'second.form.submit': 'ही पॉलिसी जोडा',

  'insured.title': 'कोणाकोणाचे कवर आहे',
  'insured.period': '{from} ते {to} पर्यंतचे कवर',
  'insured.period.open': '{from} पासून कवर',
  'insured.ending':
    'हे पॉलिसी वर्ष {days} दिवसांत संपत आहे. नूतनीकरणानंतर तुमचे कवर पुन्हा सुरू होते, त्यामुळे त्या तारखेच्या अलीकडची-पलीकडची भरती वेगवेगळ्या वर्षाच्या कवरवर जाते.',
  'insured.ended':
    'हे पॉलिसी वर्ष संपले आहे. या आकड्यांवर विसंबण्याआधी नूतनीकरण झाले होते का ते पाहा.',

  'waiting.title': 'प्रतीक्षा कालावधी',
  'waiting.served': 'पूर्ण झाली. {date} पासून कवर आहे.',
  'waiting.from': '{date} पासून कवर.',
  'waiting.no_start':
    'ही पॉलिसी कधी सुरू झाली हे आम्हाला वाचता आले नाही, त्यामुळे या अजून लागू आहेत का ते सांगता येत नाही. उपचार निवडल्यावर तुम्हाला विचारले जाईल.',
  'waiting.pending':
    'दाखवलेल्या तारखेआधी केलेला दावा नाकारला जाईल. तुम्ही निवडलेल्या उपचारानुसार आम्ही हे तपासतो.',

  'fact.correct.label': '{field} दुरुस्त करा',
  'fact.correct': 'हे दुरुस्त करा',
  'fact.saving': 'जतन होत आहे…',
  'fact.save': 'जतन करा',
  'fact.cancel': 'राहू द्या',

  'ask.placeholder.percent': 'उदा 10%, किंवा दहा टक्के',
  'ask.placeholder.amount': 'उदा 5 लाख, 5,00,000, किंवा मर्यादा नाही',
  'ask.confirming': 'फक्त खात्री करून घेऊ',
  'ask.title': 'तुमच्याकडून एक गोष्ट जाणून घ्यायची आहे',
  'ask.remaining': 'यानंतर आणखी {count}',
  'ask.page': 'आम्ही तुमच्या कागदपत्राचे पान {page} पाहत होतो.',
  'ask.source.page': '{source} मधून, पान {page}',
  'ask.source': '{source} मधून',
  'ask.other': 'यापैकी काहीही नाही, मी सांगतो',
  'ask.reading': 'वाचले जात आहे…',
  'ask.confirm': 'खात्री करा',
  'ask.free_text':
    'तुमच्या कागदपत्रात जसे लिहिले आहे तसेच लिहा, शब्दांत किंवा आकड्यांत. वापरण्याआधी आम्ही ते तुम्हाला वाचून दाखवू.',
  'ask.skip': 'हे मला माहीत नाही',
  'ask.skip.hint': 'आम्ही पुढे जाऊ आणि जिथे खात्री नसेल तिथे तसे सांगू.',

  'evidence.title': 'हे आकडे कुठून आले',
  'evidence.count': 'तुमच्या कागदपत्रातून वाचलेले {count} भाग',
  'evidence.hide': 'लपवा',
  'evidence.show': 'पाहा',
  'evidence.page': 'पान {page}',
  'evidence.uncertain': 'खात्री नाही',

  'search.title': 'तुम्हाला कोणता उपचार हवा आहे?',
  'search.subtitle':
    'ते करणारी रुग्णालये आम्ही शोधू, आणि प्रत्येकात तुम्हाला किती द्यावे लागेल ते सांगू.',
  'search.treatment': 'उपचार',
  'search.treatment.hint':
    'तुम्हाला जे सांगितले तेच लिहा. ते आम्ही सर्वात जवळच्या उपचाराशी जुळवू, ज्याचा खर्च आम्ही काढू शकतो.',
  'search.patient': 'कोणावर उपचार होणार आहे?',
  'search.patient.hint':
    'तुमची पॉलिसी फक्त मोठ्या वयाच्या सदस्यांवर वाटा घेते, त्यामुळे यामुळे आकडे बदलतात.',
  'search.patient.unsure': 'अजून नक्की नाही',
  'search.city': 'शहर',
  'search.city.count': '{city} ({count} रुग्णालये)',
  'search.distance': 'तुम्ही किती दूर जाऊ शकता?',
  'search.distance.upto': '{km} किमी पर्यंत',
  'search.preference': 'तुमच्यासाठी सर्वात महत्त्वाचे काय आहे?',
  'search.urgency': 'किती लवकर?',
  'search.urgency.planned': 'आधीच ठरलेले',
  'search.urgency.urgent': 'काही दिवसांत',
  'search.urgency.emergency': 'आपत्कालीन',
  'search.searching': 'शोधले जात आहे…',
  'search.go': 'माझे पर्याय दाखवा',

  'preference.protect_money': 'माझा खर्च कमी राहावा',
  'preference.best_care': 'सर्वोत्तम सुविधा असलेले रुग्णालय',
  'preference.nearest': 'सर्वात लवकर पोहोचावे',
  'preference.balanced': 'संतुलित',

  'eligibility.declined': 'तुमची विमा कंपनी हा दावा नाकारेल',
  'eligibility.declined.hint': 'खालील खर्च तुम्हालाच द्यावे लागतील.',
  'eligibility.one_answer': 'एका उत्तराने हे ठरेल.',
  'eligibility.why_ask':
    'कोणत्याही पॉलिसीत हे लिहिलेले नाही, आणि यामुळे उत्तर बदलते, म्हणून विचारावे लागत आहे. तुमचे उत्तर याच डिव्हाइसवर राहते.',
  'eligibility.had_before': 'होय, हे आधीपासून होते',
  'eligibility.came_after': 'नाही, हे नंतर झाले',
  'eligibility.accident': 'हा अपघात होता',

  'results.looked_at.city': 'आम्ही {city} मधील {count} रुग्णालये पाहिली.',
  'results.looked_at': 'आम्ही {count} रुग्णालये पाहिली.',
  'results.relaxed': 'ही मिळण्यासाठी आम्हाला तुमच्या अटी थोड्या सैल कराव्या लागल्या',
  'results.excluded': 'बाकीची रुग्णालये का वगळली गेली',
  'results.filter': 'नाव किंवा भागावरून रुग्णालय शोधा',
  'results.filter.label': 'हे निकाल रुग्णालयाच्या नावाने किंवा भागाने गाळा',
  'results.filter.none': '"{query}" ने इथे कोणतेही रुग्णालय सापडले नाही.',
  'results.filter.some': '{total} पैकी {shown} "{query}" शी जुळतात.',
  'results.strong': 'चांगला पर्याय',
  'results.travel': 'सुमारे {minutes} मिनिटे',
  'results.you_would_pay': 'तुम्ही द्याल',
  'results.up_to': 'जास्तीत जास्त',
  'results.up_to.driver': '{driver} झाल्यास',
  'results.hospital_bill': 'रुग्णालयाचे बिल',
  'results.insurer_pays_short': 'विमा कंपनी देईल',
  'results.upfront': 'आधी तुम्हाला द्यावे लागेल',
  'results.settlement': 'भरणा करण्याची पद्धत',
  'results.room': 'खोली',
  'results.room.rate': '{room}, रोज {rate}',
  'results.hide_breakdown': 'तपशील लपवा',
  'results.show_breakdown': 'माझे पैसे कुठे जातात?',
  'results.track': 'माझा उपचार इथेच पाहा',

  'exclusion.too_far': 'तुमच्या अंतर मर्यादेबाहेर',
  'exclusion.procedure_unavailable': 'हा उपचार करत नाहीत',
  'exclusion.specialty_unavailable': 'हा विभाग नाही',
  'exclusion.not_cashless': 'तुमच्या कॅशलेस नेटवर्कमध्ये नाही',
  'exclusion.no_bed_available': 'आत्ता खाट रिकामी नाही',
  'exclusion.no_eligible_room': 'तुमच्या दर्जाची खोली नाही',
  'exclusion.scheme_not_empanelled': 'तुमच्या योजनेसाठी सूचीबद्ध नाही',

  'room.general_ward': 'जनरल वॉर्ड',
  'room.twin_sharing': 'दोघांची खोली',
  'room.single_private': 'एकट्याची खोली',
  'room.deluxe': 'डीलक्स खोली',
  'room.suite': 'सुईट',
  'room.icu': 'ICU',

  'settlement.cashless': 'कॅशलेस',
  'settlement.reimbursement': 'आधी स्वतः द्या, नंतर दावा करा',
  'settlement.scheme_package': 'योजनेचे पॅकेज',

  'waterfall.title': 'रुग्णालयाच्या बिलापासून तुमच्या खर्चापर्यंत',
  'waterfall.lines': 'रुग्णालयाचे बिल, एक-एक बाब',

  'journey.title': 'तुमचा उपचार',
  'journey.per_day': 'रोज ₹{amount}',
  'journey.preauth.file': 'पूर्व-मंजुरी पाठवली आहे असे नोंदवा',
  'journey.timeline.skipped': '{stages} वगळले गेले.',
  'journey.charges.count': '{count} नोंदवले, एकूण {total}',
  'journey.charge.options': '{head} चे पर्याय',
  'journey.charge.close_menu': 'मेनू बंद करा',
  'journey.charge.edit': 'बदला',
  'journey.charge.delete': 'काढा',
  'journey.charge.head': 'हे कशासाठी आहे?',
  'journey.charge.amount': 'रक्कम',
  'journey.charge.when': 'केव्हा',
  'journey.charge.save': 'जतन करा',
  'journey.charge.cancel': 'बंद करा',
  'journey.charge.new_day': 'हा उपचाराचा नवीन दिवस आहे',
  'journey.charge.add': 'खर्च जोडा',
  'journey.add_charge.hint': 'बिले येतील तशी नोंदवत जा, म्हणजे अंदाज बरोबर राहील.',
  'journey.receipt.too_large':
    'ही फाइल {size} MB ची आहे. आम्ही जास्तीत जास्त {limit} MB घेऊ शकतो.',
  'journey.receipt.remove': 'काढा',
  'journey.receipt.attach': 'बिल किंवा पावती जोडा (आवश्यक नाही)',
  'journey.checklist.count': '{total} पैकी {done}',
  'journey.checklist.now': 'आत्ता',
  'journey.position.you_pay': 'आतापर्यंत तुम्ही द्याल',
  'journey.position.split':
    'रुग्णालयाने {billed} चे बिल केले आहे. त्यातील {covered} तुमची विमा कंपनी देईल.',
  'journey.position.hide': 'फरक कुठून येतो ते लपवा',
  'journey.position.show': 'फरक कुठून येतो ते पाहा',
  'journey.burn.used': 'आतापर्यंत वापरलेले कवर',
  'journey.burn.of': '{total} पैकी {used}',
  'journey.burn.left': '{amount} शिल्लक',
  'journey.burn.rate': 'रोज {amount}',
  'journey.burn.reached': 'कवर आजच संपले',
  'journey.burn.days_left': 'सुमारे {days} दिवसांचे कवर शिल्लक आहे',
  'journey.advance.settled': 'तुमचा दावा निकाली निघाला',
  'journey.advance.title': 'आत्ता तुम्ही कुठे आहात?',
  'journey.advance.settled.hint':
    'काही बदलले तर तुम्ही आताही मागच्या टप्प्यावर जाऊ शकता.',
  'journey.advance.hint':
    'गोष्टी पुढे सरकतील तसे हे बदलत राहा. तुम्ही कधीही मागे जाऊ शकता.',
  'journey.advance.stage': 'टप्पा',
  'journey.advance.here': 'तुम्ही इथे आहात',
  'journey.advance.back': 'मागे जा',
  'journey.advance.back.hint':
    'यामुळे तुमचा उपचार {stage} वर परत जाईल. तुम्ही नोंदवलेले काहीही जाणार नाही.',
  'journey.advance.go_back': 'या टप्प्यावर परत जा',
  'journey.advance.update': 'बदला',
  'journey.skip.cancel': 'राहू द्या',
  'journey.skip.title': 'फक्त सांगून ठेवतो',
  'journey.skip.body': 'थेट {stage} वर गेल्यास {skipped} वगळले जातात.',
  'journey.skip.reassure':
    'हे बऱ्याचदा अगदी बरोबरच असते. अनेक भरतींमध्ये यांपैकी काही येतच नाहीत. तुमचा अंदाज दोन्ही बाबतीत बरोबर राहतो, आणि तुम्ही नंतर कोणत्याही टप्प्यावर परत येऊ शकता.',
  'journey.skip.note': 'कारण लिहायचे आहे (आवश्यक नाही)',
  'journey.skip.placeholder':
    'उदा: आपत्कालीन स्थितीत भरती झालो, त्यामुळे पूर्व-मंजुरीला वेळ मिळाला नाही.',
  'journey.skip.confirm': '{stage} वर जा',
  'journey.skip.decline': 'आत्ता नको',

  'head.room_rent': 'खोलीचे भाडे',
  'head.icu_charges': 'ICU चा खर्च',
  'head.investigations': 'तपासण्या आणि स्कॅन',
  'head.pharmacy': 'औषधे',
  'head.consumables': 'वापरण्याचे साहित्य',
  'head.surgeon_fee': 'सर्जनची फी',
  'head.ot_charges': 'ऑपरेशन थिएटर',
  'head.nursing': 'नर्सिंग',
  'head.implants': 'इम्प्लांट',
  'head.non_medical': 'वैद्यकीय नसलेल्या वस्तू',

  'list.a_stage': 'एक टप्पा',
  'list.and': 'आणि',

  'bill.what_we_do':
    'एक-एक बाबीचे बिल मागा, एका ओळीतील एकूण नाही, आणि त्याचा फोटो घ्या. आम्ही ते ओळ-ओळ वाचून सांगतो की सही करण्याआधी काय विचारण्यासारखे आहे: नियामकाच्या मते आधीच दुसऱ्या खर्चात समाविष्ट असलेल्या बाबी, दोनदा लिहिलेल्या ओळी, गुणाकाराशी न जुळणारे आकडे, आणि तुमची विमा कंपनी करणार असलेली पण बिलिंग काउंटर न सांगणारी कपात.',
  'bill.photo_hint':
    'समोरून, चांगल्या प्रकाशात. बिलिंग काउंटरवरून मिळालेली PDF अगदी बरोबर वाचली जाते.',
  'bill.settles_to.hint': 'अंदाजातील तीच गणना, खऱ्या बिलावर लावली.',
  'bill.col.line': 'क्रम',
  'bill.col.item': 'बाब',
  'bill.col.head': 'शीर्ष',
  'bill.col.amount': 'रक्कम',

  'settings.close': 'सेटिंग बंद करा',
  'settings.close.short': 'बंद करा',
  'settings.theme.label': 'रंगरूप',
  'settings.theme.hint': '"सिस्टम" तुमच्या फोन किंवा संगणकानुसार चालते.',
  'settings.theme.light': 'उजळ',
  'settings.theme.dark': 'गडद',
  'settings.theme.system': 'सिस्टम',
  'settings.text_size.hint':
    'संपूर्ण ॲपमध्ये मोठी अक्षरे, जेणेकरून घाईत फोनवर वाचता येईल.',
  'settings.text_size.default': 'सामान्य',
  'settings.text_size.large': 'मोठे',
  'settings.session': 'हे सत्र',
  'settings.session.hint':
    'तुमची पॉलिसी आणि तुमच्यासाठी मिळालेली रुग्णालये फक्त हा टॅब उघडा असेपर्यंत ठेवली जातात. पान पुन्हा लोड केल्यास सर्व सुरुवातीपासून होते.',
  'settings.clear.yes': 'होय, पुसून टाका',
  'settings.clear.no': 'राहू द्या',
  'settings.clear': 'पुसून सुरुवातीपासून करा',
  'settings.developer': 'डेव्हलपर',
  'settings.developer.note': 'तपासणीसाठी. इथल्या कशानेही ॲपची गणना बदलत नाही.',
  'settings.activity': 'हालचाल पॅनेल दाखवा',
  'settings.activity.hint':
    'प्रत्येक पायरीचे थेट दर्शन, वेळेसह. सर्व्हर आपल्या लॉगमध्ये लिहितो त्याच घटना.',
  'settings.api': 'API',
  'settings.api.reachable': 'उपलब्ध आहे',
  'settings.api.unreachable': 'उपलब्ध नाही',
  'settings.reset': 'सेटिंग सुरुवातीच्या स्थितीत आणा',

  disclaimer:
    'हे अंदाज केवळ मार्गदर्शनासाठी आहेत. हे कोटेशन नाही, मंजुरी नाही, आणि वैद्यकीय सल्लाही नाही. सर्व रकमा तुमच्या विमा कंपनीकडून आणि रुग्णालयाच्या विमा काउंटरवर तपासून घ्या.',
}

const te = {
  'nav.start_over': 'మళ్లీ మొదలుపెట్టండి',
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

  'help.open': 'సహాయం',
  'help.title': 'సహాయం',
  'help.close': 'సహాయం మూసివేయండి',
  'help.new_chat': 'కొత్త సంభాషణ',
  'help.recentre': 'మధ్యకు తీసుకురండి',
  'help.thinking': 'చూస్తున్నాం',
  'help.placeholder': 'ఈ స్క్రీన్ గురించి ఏదైనా అడగండి',
  'help.send': 'అడగండి',
  'help.raise': 'దీన్ని బృందానికి చేరవేయండి',
  'help.ticket_title': 'బృందానికి చేరవేయండి',
  'help.ticket_subject': 'ఒకే వాక్యంలో',
  'help.ticket_detail': 'ఇంకా ఏమైనా చెప్పాలంటే',
  'help.file': 'పంపండి',
  'help.filing': 'పంపుతున్నాం',
  'help.cancel': 'వద్దు',
  'help.footer':
    'ఇది కేవలం మార్గదర్శనం, వైద్య సలహా కాదు, మరియు ఇది మీ చికిత్సలో దేనినీ మార్చలేదు. మూసివేసిన వెంటనే ఇక్కడి సంభాషణ చెరిగిపోతుంది.',
  'settings.tickets': 'మీ టికెట్లు',
  'settings.tickets.none':
    'ఇంకా ఏమీ పంపలేదు. సహాయ విండో నుండి మీరు పంపినవి ఇక్కడ వాటి సంఖ్యతో కనిపిస్తాయి.',
  'settings.tickets.stage': 'అందింది',
  'settings.tickets.note':
    'దీనిపై ఇంకా ఏ పనీ మొదలవలేదు, మరియు తప్పుడు భ్రమ కలిగించే స్థితి కంటే ఇలా చెప్పడమే మేలు',
  'settings.language': 'భాష',
  'settings.language.hint':
    'ఇది యాప్ సొంత భాషను మారుస్తుంది. మీ పాలసీ నుండి చదివినది పత్రం భాషలోనే ఉంటుంది.',
  'settings.theme': 'రూపం',
  'settings.text_size': 'అక్షరాల పరిమాణం',

  'nav.home': 'మీ చికిత్సలు',
  'nav.steps': '{count} దశలు',
  'nav.text.normal': 'సాధారణ అక్షర పరిమాణానికి తీసుకురండి',
  'nav.text.larger': 'అక్షరాలను పెద్దవి చేయండి',
  'nav.settings': 'సెట్టింగ్‌లు',
  'nav.sections': 'విభాగాలు',

  'signin.placeholder': 'మీ పేరు, లేదా మీకు గుర్తుండే ఏదైనా',

  'home.resume': 'ఆపిన చోటి నుంచే కొనసాగండి, లేదా కొత్త చేరిక మొదలుపెట్టండి.',
  'home.first': 'పాలసీ చదివించడంతో మొదలుపెట్టండి. ఆ తర్వాతదంతా ఇక్కడే భద్రపరచబడుతుంది.',
  'home.switch_user': 'మీరు కాదా?',
  'home.policy_read': 'పాలసీ చదవబడింది',
  'home.delete': '{stay} తొలగించండి',
  'home.delete.short': 'తొలగించు',
  'home.stored_locally':
    'ఇవి ఈ పరికరంలో మాత్రమే ఉంటాయి. బ్రౌజర్ డేటా తొలగిస్తే ఇవి పోతాయి.',

  'restore.opening':
    'మీ చికిత్సను తెరుస్తున్నాం. సర్వర్ మేల్కొనడానికి కొంత సమయం పట్టవచ్చు.',

  'reading.policy': 'మీ పాలసీ చదువుతున్నాం',
  'reading.policy.waiting': 'మీ ఫైళ్లను పంపుతున్నాం. ఈ పేజీని తెరిచి ఉంచండి.',
  'reading.policy.hint':
    'పొడవైన పత్రాలు, ఫోన్ ఫోటోలు ఎక్కువ సమయం తీసుకుంటాయి. దీన్ని వెనుక తెరిచి ఉంచవచ్చు.',
  'reading.search': 'మీ ఎంపికలను వెతుకుతున్నాం',
  'reading.search.hint':
    'పరిధిలోని ప్రతి ఆసుపత్రి ఖర్చును మీ పాలసీ ప్రకారం ఒక్కొక్కటిగా లెక్కిస్తున్నాం.',
  'reading.bill': 'మీ బిల్లు చదువుతున్నాం',
  'reading.bill.waiting': 'బిల్లు పంపుతున్నాం. ఈ పేజీని తెరిచి ఉంచండి.',
  'reading.bill.hint':
    'ఫోటోకు PDF కంటే ఎక్కువ సమయం పడుతుంది, ఎందుకంటే తనిఖీ చేసే ముందు ప్రతి పంక్తినీ గుర్తించాలి.',

  'locked.policy': 'మీ కవర్',
  'locked.policy.why':
    'పాలసీ చదివాక, మీకు దేనికెల్లా కవర్ ఉందో ఇక్కడ కనిపిస్తుంది, మేము తప్పుగా చదివినదాన్ని మీరు సరిచేయవచ్చు.',
  'locked.search': 'ఆసుపత్రులు',
  'locked.search.why':
    'మేము పరిధిలోని ప్రతి ఆసుపత్రి ఖర్చును మీ సొంత పాలసీ ప్రకారం లెక్కిస్తాం, కాబట్టి ముందు మీ కవర్ కావాలి.',

  'gone.title': 'ఈ చికిత్స ఈ పరికరంలో లేదు',
  'gone.why':
    'చికిత్సలు అవి మొదలైన పరికరంలోనే భద్రపరచబడతాయి. ఈ లింక్ వేరే ఫోన్ లేదా వేరే బ్రౌజర్ నుండి వచ్చినట్లయితే, ఆ చేరిక అక్కడే ఉంది, ఇక్కడ కాదు.',
  'gone.home': 'మీ చికిత్సలు',
  'gone.new': 'కొత్త చికిత్స మొదలుపెట్టండి',

  'rail.cover': 'మీ కవర్',
  'rail.check': 'మేము చదివినది చూడండి',
  'rail.room': 'కవర్ ఉన్న గది',
  'rail.treatment': 'చికిత్స',
  'rail.cheapest': 'మీకు అత్యంత చౌకైనది',
  'rail.title': 'ఇప్పటివరకు',
  'rail.change': 'మార్చండి',

  'activity.title': 'కార్యకలాపం',
  'activity.subtitle': 'వ్యవస్థ వేసే ప్రతి అడుగు',
  'activity.live': 'ప్రత్యక్షం',
  'activity.idle': 'ఆగి ఉంది',
  'activity.empty': 'పాలసీ చదువుతున్న కొద్దీ ఇక్కడ అడుగులు కనిపిస్తాయి.',
  'activity.count': '{count} దశలు',
  'activity.attention': '{count} పై దృష్టి కావాలి',

  'time.now': 'ఇప్పుడే',
  'time.minutes': '{count} నిమిషాల క్రితం',
  'time.hours': '{count} గంటల క్రితం',
  'time.yesterday': 'నిన్న',
  'time.days': '{count} రోజుల క్రితం',

  'error.dismiss': 'మూసివేయి',

  'upload.title': 'మీ ఆసుపత్రి చికిత్సకు నిజంగా ఎంత ఖర్చవుతుందో తెలుసుకోండి',
  'upload.subtitle':
    'మీ ఆరోగ్య బీమా పాలసీని అప్‌లోడ్ చేయండి, ఏ ఆసుపత్రుల్లో మీకు కవర్ ఉంది, ఏ గది మీ హక్కు, మీరే ఎంత చెల్లించాలో మేము చెబుతాం.',
  'upload.tab.file': 'నా పాలసీని అప్‌లోడ్ చేయండి',
  'upload.tab.manual': 'నా దగ్గర పత్రం లేదు',
  'upload.insurer': 'మీ బీమా ఎవరితో?',
  'upload.insurer.hint':
    'దీనితో ఏ ఆసుపత్రుల్లో మీకు నగదురహిత చికిత్స లభిస్తుందో మాకు తెలుస్తుంది.',
  'upload.insurer.choose': 'మీ బీమా సంస్థను ఎంచుకోండి',
  'upload.insurer.companies': 'బీమా సంస్థలు',
  'upload.insurer.schemes': 'ప్రభుత్వ పథకాలు',
  'upload.drop': 'మీ పాలసీని ఇక్కడ వదలండి, లేదా ఎంచుకోవడానికి నొక్కండి',
  'upload.drop.more': 'మరో పేజీ జోడించండి, లేదా ఎంచుకోవడానికి నొక్కండి',
  'upload.drop.hint':
    'PDF, ఫోటోలు రెండూ పనిచేస్తాయి, మీరు అనేకం జోడించవచ్చు. ఫోన్‌లో తీసిన ప్రతి పేజీ ఫోటో కూడా సరిపోతుంది; మేము వాటిని చదివి కలుపుతాం.',
  'upload.too_many':
    'ఇది {limit} ఫైళ్ల కంటే ఎక్కువ. మీ కవర్ రాసి ఉన్న పేజీలే సాధారణంగా సరిపోతాయి.',
  'upload.too_large':
    'ఇవి కలిపి {size} MB అవుతాయి, మేము {limit} MB వరకు చదవగలం. మీ కవర్ రాసి ఉన్న పేజీలే సాధారణంగా సరిపోతాయి.',
  'upload.remove': '{name} తీసివేయండి',
  'upload.reading': 'మీ పాలసీ చదువుతున్నాం.',
  'upload.read': 'నా పాలసీని చదవండి',
  'upload.read_many': 'ఈ {count} పత్రాలను చదవండి',
  'upload.done': 'మీ పాలసీ చదవబడింది',
  'upload.done.hint':
    'అందులో ఏముందో కింద ఉంది. ముందుకు వెళ్లే ముందు మేము తప్పుగా చదివినది సరిచేయండి.',

  'manual.sum_insured': 'మొత్తం కవర్ మొత్తం',
  'manual.sum_insured.hint': 'మీ బీమా సంస్థ సంవత్సరానికి గరిష్ఠంగా ఎంత చెల్లిస్తుంది.',
  'manual.room': 'గది అద్దె పరిమితి',
  'manual.room.hint':
    'చాలా పాలసీల్లో దీనికి పరిమితి ఉంటుంది. పరిమితి కంటే పైన గది తీసుకుంటే మిగతా ఖర్చులపైనా బీమా సంస్థ తక్కువ చెల్లిస్తుంది.',
  'manual.room.flat': 'రోజుకు నిర్ణీత మొత్తం',
  'manual.room.pct': 'నా కవర్‌లో శాతం',
  'manual.room.none': 'పరిమితి లేదు',
  'manual.room.amount': 'రోజువారీ మొత్తం',
  'manual.room.percent': 'కవర్‌లో శాతం, రోజుకు',
  'manual.copay': 'మీ వాటా',
  'manual.copay.hint':
    'ప్రతి క్లెయిమ్‌లో ఎంత వాటా మీరే చెల్లిస్తారు. లేకపోతే 0 రాయండి.',
  'manual.working': 'జరుగుతోంది…',
  'manual.continue': 'ముందుకు సాగండి',

  'treatment.placeholder': 'మీకు చెప్పినది రాయండి, ఉదా స్టెంట్, ప్రసవం, పిత్తాశయం',
  'treatment.no_match':
    'దీనికి ఏమీ దొరకలేదు. సులభమైన పదం ప్రయత్నించండి, ఉదా శరీరంలోని ఆ భాగం, లేదా డాక్టర్ చీటీలో రాసిన పదం.',

  'policy.warnings': 'మీరు అప్‌లోడ్ చేసిన పత్రం గురించి',
  'policy.title': 'మీ కవర్',
  'policy.sum_insured': 'ఈ సంవత్సరపు మొత్తం కవర్',
  'policy.sum_insured.hint': 'మీ పాలసీలో ఉన్నట్టుగా, ఉదా 5 లక్షలు లేదా 500000',
  'policy.remaining': 'ఈ సంవత్సరం మిగిలిన కవర్',
  'policy.remaining.hint':
    'ఈ పాలసీ సంవత్సరంలో ఇంతకుముందు చేసిన క్లెయిమ్ తర్వాత మిగిలినది.',
  'policy.remaining.assumed':
    'ఈ సంవత్సరం ఏ క్లెయిమూ కాలేదని మేము భావించాం. మీరు ఇప్పటికే క్లెయిమ్ చేసి ఉంటే దీన్ని సరిచేయండి: దీనితో ప్రతి అంచనా మారుతుంది.',
  'policy.remaining.restore':
    'కవర్ అయిపోతే మీ పాలసీ దాన్ని సంవత్సరానికి ఒకసారి తిరిగి నింపుతుంది.',
  'policy.room': 'కవర్ ఉన్న గది',
  'policy.room.hint': 'రోజువారీ మొత్తం, 1% వంటి శాతం, గది తరగతి, లేదా "పరిమితి లేదు"',
  'policy.room.note':
    'ఖరీదైన గది తీసుకుంటే సర్జన్, థియేటర్, నర్సింగ్ ఖర్చులపైనా బీమా సంస్థ తక్కువ చెల్లిస్తుంది.',
  'policy.copay': 'ప్రతి క్లెయిమ్‌లో మీ వాటా',
  'policy.copay.none': 'ఏమీ లేదు',
  'policy.copay.hint': 'శాతంలో, ఉదా 10. లేకపోతే 0 రాయండి.',
  'policy.copay.age':
    '{age} సంవత్సరాలు, అంతకంటే పైబడిన సభ్యులకు మాత్రమే. అంతకంటే చిన్న సభ్యుని క్లెయిమ్‌కు ఎలాంటి వాటా లేదు.',
  'policy.icu': 'ICU కవర్',
  'policy.deductible': 'ముందు మీరు చెల్లించేది',
  'policy.deductible.none': 'ఏమీ లేదు',
  'policy.deductible.hint':
    'ఇది టాప్-అప్ పాలసీల్లో మాత్రమే ఉంటుంది. మీ దాంట్లో లేకపోతే 0 రాయండి.',
  'policy.deductible.note':
    'ఇది టాప్-అప్ పాలసీ. ఇది ఈ మొత్తానికి పైన మాత్రమే చెల్లిస్తుంది.',
  'policy.consumables': 'వాడే సామగ్రి',
  'policy.covered': 'కవర్ ఉంది',
  'policy.not_covered': 'కవర్ లేదు',
  'policy.consumables.note': 'గ్లౌజులు, సిరంజీలు వంటివి మీరే చెల్లించాలి.',
  'policy.daycare': 'ఒక రోజు కంటే తక్కువ చికిత్స',
  'policy.not_stated': 'రాయలేదు',
  'policy.daycare.no':
    'కవర్‌కు పూర్తి ఒక రోజు చేరిక కావాలి. కంటిశుక్లం, డయాలసిస్ వంటి చికిత్సలకు డబ్బు రాదు.',
  'policy.daycare.unknown':
    'మీ పత్రంలో ఇది రాయలేదు. అడిగి తెలుసుకోవడం మంచిది, ఎందుకంటే కవర్‌కు సాధారణంగా 24 గంటల చేరిక కావాలి.',
  'policy.sublimits': 'ప్రత్యేక పరిమితులు',
  'policy.continue': 'కవర్ ఉన్న ఆసుపత్రులను చూపండి',
  'policy.to_confirm': '{count} నిర్ధారించాలి',
  'policy.from_scan': 'స్కాన్ నుండి చదవబడింది',
  'policy.read_cleanly': 'స్పష్టంగా చదవబడింది',

  'scheme.cover': 'ఈ సంవత్సరపు కవర్',
  'scheme.cover.note': 'సంవత్సరానికి, కుటుంబం మొత్తానికి కలిపి.',
  'scheme.you_pay': 'జాబితాలోని ఆసుపత్రిలో మీరు ఎంత చెల్లిస్తారు',
  'scheme.you_pay.value': 'ఏమీ లేదు',
  'scheme.you_pay.note':
    'చికిత్సను నిర్ణీత ప్యాకేజీ ధరకు తీసుకుంటారు. బిల్లు కట్టడం లేదు, క్లెయిమ్ చేయడం లేదు.',
  'scheme.room': 'కలిసి ఉన్న గది',
  'scheme.room.note':
    'దీనికంటే పెద్ద గది మీ సొంత ఖర్చుతో, కానీ దానివల్ల మిగతా దేని కవర్ కూడా తగ్గదు.',
  'scheme.consumables': 'సామగ్రి, ఇంప్లాంట్లు, మందులు, పరీక్షలు',
  'scheme.consumables.value': 'ప్యాకేజీలో కలిసి ఉంది',
  'scheme.empanelled_only':
    'ఇది {scheme} కోసం జాబితాలో ఉన్న ఆసుపత్రిలో మాత్రమే పనిచేస్తుంది. మరెక్కడా ఈ పథకం ఏమీ ఇవ్వదు, తర్వాత క్లెయిమ్ కూడా ఉండదు. మేము చూపే ఆసుపత్రులను ఇదే ఆధారంగా ఎంచుకున్నాం.',

  'second.title': 'మీ రెండో పాలసీ',
  'second.remove': 'తీసివేయి',
  'second.cover': 'కవర్',
  'second.room': 'గది',
  'second.above': 'దీనికి పైన మాత్రమే చెల్లిస్తుంది',
  'second.topup.how':
    'టాప్-అప్ అంటే పైన ఉన్న పరిమితి వరకు కవర్ అయిన తర్వాత మిగిలేది చెల్లించేది. మేము ముందు మీ మొదటి పాలసీని లెక్కించి, మిగిలిన మొత్తానికి దీన్ని వాడతాం.',
  'second.how':
    'మేము ఒక పాలసీని లెక్కించి, మిగిలిన మొత్తాన్ని రెండోదానికి వేస్తాం, ఏ క్రమంలో మీ ఖర్చు తక్కువో చెబుతాం.',
  'second.add': '+ నా దగ్గర మరో పాలసీ ఉంది',
  'second.add.why':
    'ఉద్యోగ కవర్, లేదా టాప్-అప్. రెండో పాలసీ మొదటిది వదిలేసినది చెల్లిస్తుంది, చాలామంది దాని నుంచి క్లెయిమే చేయరు.',
  'second.other': 'మీ మరో పాలసీ',
  'second.cancel': 'వద్దు',
  'second.form.insurer': 'ఇది ఎవరితో?',
  'second.form.insurer.hint': 'బీమా సంస్థ పేరు, లేదా మీ కార్యాలయం పేరు.',
  'second.form.insurer.placeholder': 'ఉదా మా కార్యాలయ గ్రూప్ పాలసీ',
  'second.form.cover': 'ఎంత కవర్?',
  'second.form.room': 'గది అద్దె పరిమితి',
  'second.form.room.none': 'పరిమితి లేదు',
  'second.form.room.flat': 'రోజుకు నిర్ణీత మొత్తం',
  'second.form.room.amount': 'రోజువారీ మొత్తం',
  'second.form.deductible': 'ఇది ఒక మొత్తానికి పైన మాత్రమే చెల్లిస్తుందా?',
  'second.form.deductible.hint':
    'టాప్-అప్ పాలసీలు అలా చేస్తాయి. మీది చేయకపోతే 0 గానే ఉంచండి.',
  'second.form.adding': 'జోడిస్తున్నాం…',
  'second.form.submit': 'ఈ పాలసీని జోడించండి',

  'insured.title': 'ఎవరెవరికి కవర్ ఉంది',
  'insured.period': '{from} నుంచి {to} వరకు కవర్',
  'insured.period.open': '{from} నుంచి కవర్',
  'insured.ending':
    'ఈ పాలసీ సంవత్సరం {days} రోజుల్లో ముగుస్తుంది. పునరుద్ధరణ తర్వాత మీ కవర్ మళ్లీ మొదలవుతుంది, కాబట్టి ఆ తేదీకి అటూ ఇటూ జరిగే చేరిక వేర్వేరు సంవత్సరాల కవర్‌పై పడుతుంది.',
  'insured.ended':
    'ఈ పాలసీ సంవత్సరం ముగిసింది. ఈ అంకెలను నమ్మే ముందు పునరుద్ధరణ జరిగిందా చూడండి.',

  'waiting.title': 'నిరీక్షణ కాలం',
  'waiting.served': 'పూర్తయింది. {date} నుంచి కవర్ ఉంది.',
  'waiting.from': '{date} నుంచి కవర్.',
  'waiting.no_start':
    'ఈ పాలసీ ఎప్పుడు మొదలైందో మేము చదవలేకపోయాం, కాబట్టి ఇవి ఇప్పటికీ వర్తిస్తాయా అని చెప్పలేం. చికిత్స ఎంచుకున్నప్పుడు మిమ్మల్ని అడుగుతాం.',
  'waiting.pending':
    'చూపిన తేదీకి ముందు చేసిన క్లెయిమ్ తిరస్కరించబడుతుంది. మీరు ఎంచుకున్న చికిత్సకు అనుగుణంగా మేము దీన్ని తనిఖీ చేస్తాం.',

  'fact.correct.label': '{field} సరిచేయండి',
  'fact.correct': 'దీన్ని సరిచేయండి',
  'fact.saving': 'భద్రపరుస్తున్నాం…',
  'fact.save': 'భద్రపరచు',
  'fact.cancel': 'వద్దు',

  'ask.placeholder.percent': 'ఉదా 10%, లేదా పది శాతం',
  'ask.placeholder.amount': 'ఉదా 5 లక్షలు, 5,00,000, లేదా పరిమితి లేదు',
  'ask.confirming': 'ఒకసారి నిర్ధారించుకుందాం',
  'ask.title': 'మీ నుంచి ఒక విషయం తెలియాలి',
  'ask.remaining': 'దీని తర్వాత ఇంకా {count}',
  'ask.page': 'మేము మీ పత్రంలోని పేజీ {page} చూస్తున్నాం.',
  'ask.source.page': '{source} నుంచి, పేజీ {page}',
  'ask.source': '{source} నుంచి',
  'ask.other': 'వీటిలో ఏదీ కాదు, నేనే చెబుతాను',
  'ask.reading': 'చదువుతున్నాం…',
  'ask.confirm': 'నిర్ధారించు',
  'ask.free_text':
    'మీ పత్రంలో ఉన్నట్టుగానే రాయండి, పదాల్లో లేదా అంకెల్లో. వాడే ముందు మేము దాన్ని మీకు చదివి చూపిస్తాం.',
  'ask.skip': 'ఇది నాకు తెలియదు',
  'ask.skip.hint': 'మేము ముందుకు సాగుతాం, ఎక్కడ ఖచ్చితత్వం లేదో అక్కడ చెబుతాం.',

  'evidence.title': 'ఈ అంకెలు ఎక్కడి నుంచి వచ్చాయి',
  'evidence.count': 'మీ పత్రం నుంచి చదివిన {count} భాగాలు',
  'evidence.hide': 'దాచు',
  'evidence.show': 'చూడు',
  'evidence.page': 'పేజీ {page}',
  'evidence.uncertain': 'ఖచ్చితం కాదు',

  'search.title': 'మీకు ఏ చికిత్స కావాలి?',
  'search.subtitle':
    'అది చేసే ఆసుపత్రులను మేము వెతుకుతాం, ప్రతిదానిలో మీరు ఎంత చెల్లించాలో చెబుతాం.',
  'search.treatment': 'చికిత్స',
  'search.treatment.hint':
    'మీకు చెప్పినదే రాయండి. దాన్ని మేము దగ్గరి చికిత్సతో సరిపోలుస్తాం, దాని ఖర్చు మేము లెక్కించగలం.',
  'search.patient': 'ఎవరికి చికిత్స?',
  'search.patient.hint':
    'మీ పాలసీ పెద్ద వయసు సభ్యులపై మాత్రమే వాటా తీసుకుంటుంది, కాబట్టి దీనితో అంకెలు మారతాయి.',
  'search.patient.unsure': 'ఇంకా ఖచ్చితం కాదు',
  'search.city': 'నగరం',
  'search.city.count': '{city} ({count} ఆసుపత్రులు)',
  'search.distance': 'మీరు ఎంత దూరం వెళ్లగలరు?',
  'search.distance.upto': '{km} కిమీ వరకు',
  'search.preference': 'మీకు అత్యంత ముఖ్యమైనది ఏమిటి?',
  'search.urgency': 'ఎంత త్వరగా?',
  'search.urgency.planned': 'ముందే నిర్ణయించినది',
  'search.urgency.urgent': 'కొన్ని రోజుల్లో',
  'search.urgency.emergency': 'అత్యవసరం',
  'search.searching': 'వెతుకుతున్నాం…',
  'search.go': 'నా ఎంపికలను చూపండి',

  'preference.protect_money': 'నా ఖర్చు తక్కువగా ఉండాలి',
  'preference.best_care': 'ఉత్తమ సౌకర్యాలున్న ఆసుపత్రి',
  'preference.nearest': 'త్వరగా చేరుకోవాలి',
  'preference.balanced': 'సమతుల్యం',

  'eligibility.declined': 'మీ బీమా సంస్థ ఈ క్లెయిమ్‌ను తిరస్కరిస్తుంది',
  'eligibility.declined.hint': 'కింది ఖర్చులు మీరే చెల్లించాలి.',
  'eligibility.one_answer': 'ఒక సమాధానంతో ఇది తేలుతుంది.',
  'eligibility.why_ask':
    'ఏ పాలసీలోనూ ఇది రాయలేదు, దీనితో సమాధానం మారుతుంది, అందుకే అడగాల్సి వస్తోంది. మీ సమాధానం ఈ పరికరంలోనే ఉంటుంది.',
  'eligibility.had_before': 'అవును, ఇది ముందు నుంచే ఉంది',
  'eligibility.came_after': 'కాదు, ఇది తర్వాత వచ్చింది',
  'eligibility.accident': 'ఇది ప్రమాదం',

  'results.looked_at.city': 'మేము {city}లోని {count} ఆసుపత్రులను చూశాం.',
  'results.looked_at': 'మేము {count} ఆసుపత్రులను చూశాం.',
  'results.relaxed': 'ఇవి దొరకడానికి మేము మీ షరతులను కొంత సడలించాల్సి వచ్చింది',
  'results.excluded': 'మిగతా ఆసుపత్రులు ఎందుకు మిగిలిపోయాయి',
  'results.filter': 'పేరు లేదా ప్రాంతం ద్వారా ఆసుపత్రిని వెతకండి',
  'results.filter.label': 'ఈ ఫలితాలను ఆసుపత్రి పేరు లేదా ప్రాంతం ద్వారా వడపోయండి',
  'results.filter.none': '"{query}"కు ఇక్కడ ఏ ఆసుపత్రీ దొరకలేదు.',
  'results.filter.some': '{total}లో {shown} "{query}"కు సరిపోతాయి.',
  'results.strong': 'మంచి ఎంపిక',
  'results.travel': 'సుమారు {minutes} నిమిషాలు',
  'results.you_would_pay': 'మీరు చెల్లించేది',
  'results.up_to': 'గరిష్ఠంగా',
  'results.up_to.driver': '{driver} జరిగితే',
  'results.hospital_bill': 'ఆసుపత్రి బిల్లు',
  'results.insurer_pays_short': 'బీమా సంస్థ చెల్లిస్తుంది',
  'results.upfront': 'ముందు మీరు చెల్లించాలి',
  'results.settlement': 'చెల్లింపు విధానం',
  'results.room': 'గది',
  'results.room.rate': '{room}, రోజుకు {rate}',
  'results.hide_breakdown': 'వివరాలు దాచు',
  'results.show_breakdown': 'నా డబ్బు ఎక్కడికి పోతుంది?',
  'results.track': 'నా చికిత్సను ఇక్కడే చూడండి',

  'exclusion.too_far': 'మీ దూర పరిమితి బయట',
  'exclusion.procedure_unavailable': 'ఈ చికిత్స చేయరు',
  'exclusion.specialty_unavailable': 'ఈ విభాగం లేదు',
  'exclusion.not_cashless': 'మీ నగదురహిత నెట్‌వర్క్‌లో లేదు',
  'exclusion.no_bed_available': 'ఇప్పుడు పడక ఖాళీ లేదు',
  'exclusion.no_eligible_room': 'మీ తరగతి గది లేదు',
  'exclusion.scheme_not_empanelled': 'మీ పథకం కోసం జాబితాలో లేదు',

  'room.general_ward': 'జనరల్ వార్డు',
  'room.twin_sharing': 'ఇద్దరి గది',
  'room.single_private': 'ఒంటరి గది',
  'room.deluxe': 'డీలక్స్ గది',
  'room.suite': 'సూట్',
  'room.icu': 'ICU',

  'settlement.cashless': 'నగదురహితం',
  'settlement.reimbursement': 'ముందు మీరే చెల్లించండి, తర్వాత క్లెయిమ్ చేయండి',
  'settlement.scheme_package': 'పథకం ప్యాకేజీ',

  'waterfall.title': 'ఆసుపత్రి బిల్లు నుంచి మీ ఖర్చు వరకు',
  'waterfall.lines': 'ఆసుపత్రి బిల్లు, ఒక్కొక్కటిగా',

  'journey.title': 'మీ చికిత్స',
  'journey.per_day': 'రోజుకు ₹{amount}',
  'journey.preauth.file': 'ముందస్తు అనుమతి పంపబడింది అని గుర్తించండి',
  'journey.timeline.skipped': '{stages} దాటవేయబడ్డాయి.',
  'journey.charges.count': '{count} నమోదు, మొత్తం {total}',
  'journey.charge.options': '{head} కోసం ఎంపికలు',
  'journey.charge.close_menu': 'మెనూ మూసివేయండి',
  'journey.charge.edit': 'మార్చు',
  'journey.charge.delete': 'తొలగించు',
  'journey.charge.head': 'ఇది దేని కోసం?',
  'journey.charge.amount': 'మొత్తం',
  'journey.charge.when': 'ఎప్పుడు',
  'journey.charge.save': 'భద్రపరచు',
  'journey.charge.cancel': 'మూసివేయి',
  'journey.charge.new_day': 'ఇది చికిత్స కొత్త రోజు',
  'journey.charge.add': 'ఖర్చు జోడించు',
  'journey.add_charge.hint':
    'బిల్లులు వచ్చిన కొద్దీ నమోదు చేస్తూ ఉండండి, అంచనా సరిగా ఉంటుంది.',
  'journey.receipt.too_large':
    'ఈ ఫైలు {size} MB ఉంది. మేము గరిష్ఠంగా {limit} MB తీసుకోగలం.',
  'journey.receipt.remove': 'తీసివేయి',
  'journey.receipt.attach': 'బిల్లు లేదా రసీదు జతచేయండి (తప్పనిసరి కాదు)',
  'journey.checklist.count': '{total}లో {done}',
  'journey.checklist.now': 'ఇప్పుడు',
  'journey.position.you_pay': 'ఇప్పటివరకు మీరు చెల్లించేది',
  'journey.position.split':
    'ఆసుపత్రి {billed} బిల్లు చేసింది. అందులో {covered} మీ బీమా సంస్థ చెల్లిస్తుంది.',
  'journey.position.hide': 'తేడా ఎక్కడి నుంచి వస్తుందో దాచండి',
  'journey.position.show': 'తేడా ఎక్కడి నుంచి వస్తుందో చూడండి',
  'journey.burn.used': 'ఇప్పటివరకు వాడిన కవర్',
  'journey.burn.of': '{total}లో {used}',
  'journey.burn.left': '{amount} మిగిలింది',
  'journey.burn.rate': 'రోజుకు {amount}',
  'journey.burn.reached': 'కవర్ ఈరోజే అయిపోయింది',
  'journey.burn.days_left': 'సుమారు {days} రోజుల కవర్ మిగిలింది',
  'journey.advance.settled': 'మీ క్లెయిమ్ పరిష్కారమైంది',
  'journey.advance.title': 'ఇప్పుడు మీరు ఎక్కడ ఉన్నారు?',
  'journey.advance.settled.hint': 'ఏదైనా మారితే మీరు ఇప్పటికీ మునుపటి దశకు వెళ్లవచ్చు.',
  'journey.advance.hint':
    'విషయాలు ముందుకు సాగిన కొద్దీ దీన్ని మార్చుతూ ఉండండి. మీరు ఎప్పుడైనా వెనక్కి వెళ్లవచ్చు.',
  'journey.advance.stage': 'దశ',
  'journey.advance.here': 'మీరు ఇక్కడ ఉన్నారు',
  'journey.advance.back': 'వెనక్కి వెళ్లు',
  'journey.advance.back.hint':
    'దీనితో మీ చికిత్స {stage}కు తిరిగి వెళ్తుంది. మీరు నమోదు చేసినది ఏదీ పోదు.',
  'journey.advance.go_back': 'ఈ దశకు తిరిగి వెళ్లండి',
  'journey.advance.update': 'నవీకరించు',
  'journey.skip.cancel': 'వద్దు',
  'journey.skip.title': 'ఒక్క మాట',
  'journey.skip.body': 'నేరుగా {stage}కు వెళ్తే {skipped} దాటవేయబడతాయి.',
  'journey.skip.reassure':
    'ఇది చాలాసార్లు సరైనదే. చాలా చేరికల్లో వీటిలో కొన్ని అసలు రావు. మీ అంచనా రెండు సందర్భాల్లోనూ సరిగానే ఉంటుంది, మీరు తర్వాత ఏ దశకైనా తిరిగి రావచ్చు.',
  'journey.skip.note': 'కారణం రాయాలనుకుంటున్నాను (తప్పనిసరి కాదు)',
  'journey.skip.placeholder':
    'ఉదా: అత్యవసర పరిస్థితిలో చేరాం, అందుకే ముందస్తు అనుమతికి సమయం దొరకలేదు.',
  'journey.skip.confirm': '{stage}కు వెళ్లండి',
  'journey.skip.decline': 'ఇప్పుడు కాదు',

  'head.room_rent': 'గది అద్దె',
  'head.icu_charges': 'ICU ఖర్చు',
  'head.investigations': 'పరీక్షలు, స్కాన్‌లు',
  'head.pharmacy': 'మందులు',
  'head.consumables': 'వాడే సామగ్రి',
  'head.surgeon_fee': 'సర్జన్ ఫీజు',
  'head.ot_charges': 'ఆపరేషన్ థియేటర్',
  'head.nursing': 'నర్సింగ్',
  'head.implants': 'ఇంప్లాంట్లు',
  'head.non_medical': 'వైద్యేతర వస్తువులు',

  'list.a_stage': 'ఒక దశ',
  'list.and': 'మరియు',

  'bill.what_we_do':
    'ఒక్కొక్క వస్తువు బిల్లు అడగండి, ఒకే పంక్తి మొత్తం కాదు, దాని ఫోటో తీయండి. మేము దాన్ని పంక్తి పంక్తిగా చదివి, సంతకం చేసే ముందు ఏమి అడగాలో చెబుతాం: నియంత్రణ సంస్థ ప్రకారం ఇప్పటికే మరో ఛార్జీలో కలిసి ఉన్న వస్తువులు, రెండుసార్లు రాసిన పంక్తులు, గుణించితే సరిపోని అంకెలు, మీ బీమా సంస్థ చేసే కానీ బిల్లింగ్ కౌంటర్ చెప్పని కోత.',
  'bill.photo_hint':
    'ముందు నుంచి, మంచి వెలుతురులో. బిల్లింగ్ కౌంటర్ నుంచి వచ్చిన PDF కచ్చితంగా చదవబడుతుంది.',
  'bill.settles_to.hint': 'అంచనాలో ఉన్న అదే లెక్కను నిజమైన బిల్లుపై వేశాం.',
  'bill.col.line': 'వరుస',
  'bill.col.item': 'వస్తువు',
  'bill.col.head': 'శీర్షిక',
  'bill.col.amount': 'మొత్తం',

  'settings.close': 'సెట్టింగ్‌లు మూసివేయండి',
  'settings.close.short': 'మూసివేయి',
  'settings.theme.label': 'రూపం',
  'settings.theme.hint': '"సిస్టమ్" మీ ఫోన్ లేదా కంప్యూటర్ ప్రకారం నడుస్తుంది.',
  'settings.theme.light': 'లేత',
  'settings.theme.dark': 'ముదురు',
  'settings.theme.system': 'సిస్టమ్',
  'settings.text_size.hint':
    'యాప్ మొత్తంలో పెద్ద అక్షరాలు, హడావిడిలో ఫోన్‌లో చదవగలిగేలా.',
  'settings.text_size.default': 'సాధారణం',
  'settings.text_size.large': 'పెద్దది',
  'settings.session': 'ఈ సెషన్',
  'settings.session.hint':
    'మీ పాలసీ, మీ కోసం దొరికిన ఆసుపత్రులు ఈ ట్యాబ్ తెరిచి ఉన్నంతవరకే ఉంటాయి. పేజీని మళ్లీ లోడ్ చేస్తే అంతా మొదటి నుంచి.',
  'settings.clear.yes': 'అవును, తొలగించండి',
  'settings.clear.no': 'ఉంచండి',
  'settings.clear': 'తొలగించి మొదటి నుంచి మొదలుపెట్టండి',
  'settings.developer': 'డెవలపర్',
  'settings.developer.note': 'తనిఖీ కోసం. ఇక్కడి దేనివల్లా యాప్ లెక్కింపు మారదు.',
  'settings.activity': 'కార్యకలాప ప్యానెల్ చూపండి',
  'settings.activity.hint':
    'ప్రతి దశ ప్రత్యక్ష దృశ్యం, సమయంతో సహా. సర్వర్ తన లాగ్‌లో రాసే అవే ఘటనలు.',
  'settings.api': 'API',
  'settings.api.reachable': 'అందుబాటులో ఉంది',
  'settings.api.unreachable': 'అందుబాటులో లేదు',
  'settings.reset': 'సెట్టింగ్‌లను మొదటి స్థితికి తీసుకురండి',

  disclaimer:
    'ఈ అంచనాలు మార్గదర్శనం కోసమే. ఇది కోట్ కాదు, ఆమోదం కాదు, వైద్య సలహా కాదు. అన్ని మొత్తాలను మీ బీమా సంస్థతో మరియు ఆసుపత్రి బీమా కౌంటర్‌లో నిర్ధారించుకోండి.',
}

const STRINGS = { hi, kn, mr, te }

// English is the source, so it has no table: a key with no translation renders
// the English the call site passed, which is also what a partially translated
// language does. Nothing ever renders a key.
export function translator(code) {
  const table = STRINGS[code]
  return (key, english, values) => {
    const text = (table && table[key]) || english
    if (!values) return text
    // Placeholders rather than concatenation, because the order a sentence
    // puts its figure and its noun in is not the same in every one of these
    // languages, and a translator has to be able to move them.
    return text.replace(/\{(\w+)\}/g, (whole, name) =>
      Object.hasOwn(values, name) ? String(values[name]) : whole
    )
  }
}

export function isTranslated(code) {
  return Boolean(STRINGS[code])
}
