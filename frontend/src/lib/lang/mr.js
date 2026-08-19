// Marathi (मराठी). The interface's own words, keyed to the English
// that the call site passes alongside them.
//
// Its own module so that a reader downloads one language rather than five.
// lib/i18n.js imports this on demand, when somebody asks for it, and never
// otherwise. A key here with no call site, or a call site with no key here,
// fails scripts/check-strings.mjs.

export default {
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
