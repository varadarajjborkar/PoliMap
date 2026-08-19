// Hindi (हिन्दी). The interface's own words, keyed to the English
// that the call site passes alongside them.
//
// Its own module so that a reader downloads one language rather than five.
// lib/i18n.js imports this on demand, when somebody asks for it, and never
// otherwise. A key here with no call site, or a call site with no key here,
// fails scripts/check-strings.mjs.

export default {
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
