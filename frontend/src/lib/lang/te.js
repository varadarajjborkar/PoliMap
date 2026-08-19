// Telugu (తెలుగు). The interface's own words, keyed to the English
// that the call site passes alongside them.
//
// Its own module so that a reader downloads one language rather than five.
// lib/i18n.js imports this on demand, when somebody asks for it, and never
// otherwise. A key here with no call site, or a call site with no key here,
// fails scripts/check-strings.mjs.

export default {
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
    'పాస్‌వర్డ్ లేదు, ఖాతా లేదు. మీరు టైప్ చేసినది మిమ్మల్ని గుర్తించదు, ఈ పరికరంలో వేరే పేరు వేరే చికిత్సలను తెరుస్తుంది.',
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
    'మీ కవర్, అంచనా, ఇప్పటివరకు బిల్లు, ఇంకా మిగిలినది. బీమా కౌంటర్ కోసం ఒక పేజీ.',
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
    'మార్గదర్శనం మాత్రమే, వైద్య సలహా ఎప్పుడూ కాదు, ఇది మీ అడ్మిషన్‌ను మార్చలేదు. మూసేసిన తర్వాత ఇక్కడిది ఏమీ ఉండదు.',
  'settings.tickets': 'మీ టికెట్లు',
  'settings.tickets.none':
    'ఇంకా ఏమీ లేవనెత్తలేదు. సహాయ కేంద్రం నుంచి పంపినవన్నీ ఇక్కడ కనిపిస్తాయి.',
  'settings.tickets.stage': 'అందింది',
  'settings.tickets.note':
    'దీనిపై ఇంకా ఏ పనీ మొదలవలేదు, మరియు తప్పుడు భ్రమ కలిగించే స్థితి కంటే ఇలా చెప్పడమే మేలు',
  'settings.language': 'భాష',
  'settings.language.hint':
    'ఇది యాప్ సొంత పదాలను మారుస్తుంది. మీ పాలసీ నుంచి చదివినది పత్రం రాసిన భాషలోనే ఉంటుంది.',
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
    'పొడవైన పత్రాలు, ఫోన్ ఫోటోలకు ఎక్కువ సమయం పడుతుంది. దీన్ని తెరిచే ఉంచవచ్చు.',
  'reading.search': 'మీ ఎంపికలను వెతుకుతున్నాం',
  'reading.search.hint':
    'పరిధిలోని ప్రతి ఆసుపత్రి ఖర్చును మీ పాలసీ ప్రకారం ఒక్కొక్కటిగా లెక్కిస్తున్నాం.',
  'reading.bill': 'మీ బిల్లు చదువుతున్నాం',
  'reading.bill.waiting': 'బిల్లు పంపుతున్నాం. ఈ పేజీని తెరిచి ఉంచండి.',
  'reading.bill.hint':
    'ఫోటోకు PDF కంటే ఎక్కువ సమయం: ప్రతి పంక్తినీ ముందు గుర్తించాలి.',

  'locked.policy': 'మీ కవర్',
  'locked.policy.why':
    'మీ పాలసీ చదవగానే మీ కవర్ గురించి అది చెప్పేదంతా ఇక్కడ కనిపిస్తుంది, మేము తప్పు చేస్తే మీరు సరిచేయవచ్చు.',
  'locked.search': 'ఆసుపత్రులు',
  'locked.search.why':
    'పరిధిలోని ప్రతి ఆసుపత్రి ఖర్చునూ మీ పాలసీతో లెక్కిస్తాం, కాబట్టి ముందు మీ కవర్ కావాలి.',

  'gone.title': 'ఈ చికిత్స ఈ పరికరంలో లేదు',
  'gone.why':
    'చికిత్సలు అవి తయారైన పరికరంలోనే భద్రపరచబడతాయి. ఈ లింక్ వేరే ఫోన్ లేదా బ్రౌజర్ నుంచి వస్తే, ఆ అడ్మిషన్ అక్కడే ఉంది, ఇక్కడ కాదు.',
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
    'మీ ఆరోగ్య పాలసీని అప్‌లోడ్ చేయండి. ఏ ఆసుపత్రులు మిమ్మల్ని కవర్ చేస్తాయో, ఏ గది వస్తుందో, మీరు ఎంత చెల్లిస్తారో చూపిస్తాం.',
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
    'PDF, ఫోటోలు రెండూ పనిచేస్తాయి, ఎన్నైనా జోడించవచ్చు. ప్రతి పేజీ ఫోన్ ఫోటో సరిపోతుంది; మేము వాటిని కలుపుతాం.',
  'upload.too_many':
    'ఇది {limit} ఫైళ్ల కంటే ఎక్కువ. మీ కవర్ చెప్పే పేజీలు సాధారణంగా సరిపోతాయి.',
  'upload.too_large':
    'ఇవి {size} MB అవుతున్నాయి; మేము {limit} MB వరకు చదువుతాం. మీ కవర్ చెప్పే పేజీలు సాధారణంగా సరిపోతాయి.',
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
    'చాలా పాలసీలు దీనికి పరిమితి పెడతాయి. పరిమితి పైన ఉన్న గది మిగతా ఖర్చులపై వచ్చే మొత్తాన్నీ తగ్గిస్తుంది.',
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
    'ఈ సంవత్సరం క్లెయిమ్ లేదని భావించాం. చేసి ఉంటే సరిచేయండి: ఇది ప్రతి అంచనానూ మారుస్తుంది.',
  'policy.remaining.restore':
    'కవర్ అయిపోతే మీ పాలసీ దాన్ని సంవత్సరానికి ఒకసారి తిరిగి నింపుతుంది.',
  'policy.room': 'కవర్ ఉన్న గది',
  'policy.room.hint': 'రోజువారీ మొత్తం, 1% వంటి శాతం, గది తరగతి, లేదా "పరిమితి లేదు"',
  'policy.room.note':
    'ఖరీదైన గది సర్జన్, థియేటర్, నర్సింగ్‌పై వచ్చే మొత్తాన్ని కూడా తగ్గిస్తుంది.',
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
    'కవర్‌కు పూర్తి రోజు అడ్మిషన్ కావాలి. కంటిశుక్లం, డయాలసిస్ వంటివి రావు.',
  'policy.daycare.unknown':
    'మీ పత్రం చెప్పడం లేదు. అడగడం మంచిది: కవర్‌కు సాధారణంగా 24 గంటలు కావాలి.',
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
    'చికిత్స నిర్ణీత ప్యాకేజీ ధరకు కొనబడుతుంది. బిల్లు చెల్లించనూ అక్కర్లేదు, తిరిగి అడగనూ అక్కర్లేదు.',
  'scheme.room': 'కలిసి ఉన్న గది',
  'scheme.room.note': 'పై గది మీరే చెల్లించాలి, కానీ పథకం ఇచ్చే మరేదీ తగ్గదు.',
  'scheme.consumables': 'సామగ్రి, ఇంప్లాంట్లు, మందులు, పరీక్షలు',
  'scheme.consumables.value': 'ప్యాకేజీలో కలిసి ఉంది',
  'scheme.empanelled_only':
    '{scheme}లో నమోదైన ఆసుపత్రిలో మాత్రమే. ఇతర చోట్ల అది ఏమీ ఇవ్వదు, తర్వాత క్లెయిమూ ఉండదు. కింది ఆసుపత్రులు దీని ఆధారంగానే ఎంపికయ్యాయి.',

  'second.title': 'మీ రెండో పాలసీ',
  'second.remove': 'తీసివేయి',
  'second.cover': 'కవర్',
  'second.room': 'గది',
  'second.above': 'దీనికి పైన మాత్రమే చెల్లిస్తుంది',
  'second.topup.how':
    'టాప్-అప్ దాని పైన ఉన్న పరిమితి నిండాక మిగిలినది ఇస్తుంది. ముందు మీ మొదటి పాలసీని పరిష్కరిస్తాం, తర్వాత మిగతాదానికి ఇది.',
  'second.how':
    'ఒక పాలసీని పరిష్కరించి, మిగతాదాన్ని రెండోదానికి వేసి, ఏ వరుస చౌకో చెబుతాం.',
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
    'ఈ పాలసీ సంవత్సరం ముగిసింది. ఈ అంకెలను నమ్మే ముందు రెన్యువల్ అయిందో చూడండి.',

  'waiting.title': 'నిరీక్షణ కాలం',
  'waiting.served': 'పూర్తయింది. {date} నుంచి కవర్ ఉంది.',
  'waiting.from': '{date} నుంచి కవర్.',
  'waiting.no_start':
    'ప్రారంభ తేదీని మేము చదవలేకపోయాం, కాబట్టి ఇవి ఇంకా వర్తిస్తాయో చెప్పలేం. చికిత్స ఎంచుకున్నాక అడుగుతాం.',
  'waiting.pending':
    'చూపిన తేదీ ముందు క్లెయిమ్ తిరస్కరిస్తారు. మేము దీన్ని మీ చికిత్సతో సరిచూస్తాం.',

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
    'మీ పత్రంలో ఉన్నట్లే రాయండి, మాటల్లో లేదా అంకెల్లో. మేము ముందు చదివి చూపిస్తాం.',
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
    'ఏ పాలసీ దీన్ని చెప్పదు, దీనితో సమాధానం మారుతుంది, అందుకే అడుగుతాం. ఇది ఈ పరికరంలోనే ఉంటుంది.',
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
    'ఇది తరచూ సరైనదే. చాలా అడ్మిషన్లు వీటిలో కొన్నింటిని దాటేస్తాయి. మీ అంచనా కచ్చితంగానే ఉంటుంది, ఏ దశకైనా తిరిగి రావచ్చు.',
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
    'ఒక్క లైను మొత్తం కాదు, వివరమైన బిల్లు అడిగి దాని ఫోటో తీయండి. మేము ప్రతి పంక్తినీ చదివి, సంతకం ముందు దేన్ని లేవనెత్తాలో చెబుతాం: ఇప్పటికే మరొకదానిలో ఉన్న ఛార్జీలు, రెండుసార్లు వచ్చిన పంక్తులు, గుణించని అంకెలు, బీమా సంస్థ చేసే కానీ ఎవరూ చెప్పని కోత.',
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
    'మీ పాలసీ, మీ కోసం దొరికిన ఆసుపత్రులు ఈ ట్యాబ్ తెరిచి ఉన్నంతవరకే ఉంటాయి. రీలోడ్ చేస్తే మళ్లీ మొదటి నుంచి.',
  'settings.clear.yes': 'అవును, తొలగించండి',
  'settings.clear.no': 'ఉంచండి',
  'settings.clear': 'తొలగించి మొదటి నుంచి మొదలుపెట్టండి',
  'settings.developer': 'డెవలపర్',
  'settings.developer.note': 'తనిఖీ కోసం. ఇక్కడి దేనివల్లా యాప్ లెక్కింపు మారదు.',
  'settings.activity': 'కార్యకలాప ప్యానెల్ చూపండి',
  'settings.activity.hint':
    'ప్రతి పైప్‌లైన్ దశ ప్రత్యక్ష ప్రసారం, సమయాలతో. సర్వర్ తన లాగ్‌లో రాసే అవే ఘటనలు.',
  'settings.api': 'API',
  'settings.api.reachable': 'అందుబాటులో ఉంది',
  'settings.api.unreachable': 'అందుబాటులో లేదు',
  'settings.reset': 'సెట్టింగ్‌లను మొదటి స్థితికి తీసుకురండి',

  disclaimer:
    'అంచనాలు మార్గదర్శనం కోసమే: కోట్ కాదు, ఆమోదం కాదు, వైద్య సలహా కాదు. ప్రతి మొత్తాన్నీ మీ బీమా సంస్థతో, ఆసుపత్రి బీమా కౌంటర్‌లో నిర్ధారించుకోండి.',

  // --- what the server writes -----------------------------------------------
  //
  // Composed in Python, where the policy and the bill are, and sent with the
  // key it is read under and the figures written into it. The English arrives
  // beside it, so a key with no line here still reads.

  // What to do at this stage of this admission.
  'checklist.carry_card':
    'మీ పాలసీ కార్డు, రోగి ఫోటో గుర్తింపు కార్డు తీసుకెళ్లండి',
  'checklist.carry_card.why':
    'రెండూ లేకుండా కౌంటర్ క్యాష్‌లెస్ క్లెయిమ్ మొదలుపెట్టలేదు.',
  'checklist.confirm_network':
    'ఈ చికిత్సకు ఇక్కడ {insurer} క్యాష్‌లెస్ పనిచేస్తుందా అని ఆసుపత్రిని అడగండి',
  'checklist.confirm_network.why':
    'నెట్‌వర్క్ జాబితా మారుతూ ఉంటుంది. లెక్కలోకి వచ్చేది కౌంటర్‌లోనే.',
  'checklist.ask_for_room': 'రోజుకు {cap} లేదా అంతకంటే తక్కువ ఉన్న గది అడగండి',
  'checklist.ask_for_room.why':
    'ఖరీదైన గది గదిని మాత్రమే కాదు, సర్జన్, ఆపరేషన్ థియేటర్, నర్సింగ్‌పై వచ్చే మొత్తాన్ని కూడా తగ్గిస్తుంది.',
  'checklist.gather_pre_bills':
    'గత {days} రోజుల బిల్లులు సేకరించండి: డాక్టర్, పరీక్షలు, మందులు',
  'checklist.gather_pre_bills.why':
    'వీటికి క్లెయిమ్ చేయవచ్చు, వీటినే ఎక్కువగా పారేస్తారు.',
  'checklist.expect_consumables':
    'గ్లౌజులు, సిరంజీల వంటి వాటి ఖర్చు మీదే అనుకోండి',
  'checklist.expect_consumables.why':
    'ఈ పాలసీ వీటిని ఇవ్వదు. ఆపరేషన్‌లో ఇవి తరచూ కొన్ని వేల రూపాయలవుతాయి.',
  'checklist.check_room_rate': 'అడ్మిషన్ ఫారంలో రాసిన గది ధరను చూడండి',
  'checklist.check_room_rate.why':
    'మిగతా బిల్లులో ఎంత వస్తుందో ఈ ఒక్క సంఖ్యే నిర్ణయిస్తుంది. ఇప్పుడే సరిచేయించండి; డిశ్చార్జి సమయంలో ఎవరూ చూడరు.',
  'checklist.keep_receipts': 'ప్రతి రసీదు ఉంచండి, మందుల షాపుది కూడా',
  'checklist.keep_receipts.why': 'అసలు బిల్లు లేకుండా ఏదీ తిరిగి రాదు.',
  'checklist.daily_bill': 'ప్రతిరోజూ బిల్లు అడగండి, చదవండి',
  'checklist.daily_bill.why':
    'అదే రోజు అడిగిన ఛార్జి సరిచేస్తారు. డిశ్చార్జి రోజు అడిగితే దాన్ని సమర్థిస్తారు.',
  'checklist.ask_cost_first':
    'ప్రతి పరీక్ష ఖర్చు ముందు అడగండి, తర్వాత ఒప్పుకోండి',
  'checklist.ask_cost_first.why':
    'బిల్లు అత్యంత వేగంగా పెరిగేది పరీక్షలతోనే, పరిమితి కూడా అక్కడే నిశ్శబ్దంగా దాటుతుంది.',
  'checklist.watch_the_room': 'వేరే గదికి లేదా ఐసీయూకు మార్చే ముందు అడగండి',
  'checklist.watch_the_room.why':
    'కొత్త గది అంటే కొత్త రోజువారీ ధర, గదితో ముడిపడిన ప్రతి ఖర్చుపై కొత్త వాటా.',
  'checklist.room_within_cap':
    'మీ గది బిల్లు రోజుకు {cap} లేదా తక్కువ ఉందా చూడండి',
  'checklist.room_within_cap.why':
    'మీ అడ్మిషన్ {rate} ధరతో జరిగింది. గది మార్చడం మొదటి రోజు సులభం, చివరి రోజు కష్టం.',
  'checklist.diagnostics_sublimit':
    'పరీక్షలకు మీ పాలసీ {cap} పరిమితి పెట్టిందని డాక్టర్‌కు చెప్పండి',
  'checklist.diagnostics_sublimit.why':
    'ఇప్పటివరకు వాడింది: {spent}. పరిమితి పైన ఉన్నదంతా మీదే.',
  'checklist.implant_invoice': 'ఇంప్లాంట్ బిల్లు, దాని స్టిక్కర్ అడగండి',
  'checklist.implant_invoice.why':
    'ఇంప్లాంట్ క్లెయిమ్ వేరు, తయారీదారు బిల్లు లేకుండా తిరస్కరిస్తారు. తర్వాత అది ఎక్కడా దొరకదు.',
  'checklist.consumables_running':
    'వాడే సామగ్రి జాబితా విడివిడిగా ఉంచమని వార్డుకు చెప్పండి',
  'checklist.consumables_running.why':
    'వీటికి డబ్బు మీరే ఇస్తున్నారు, కాబట్టి డిశ్చార్జి సమయంలో సరిచూసుకోవడానికి ఇదొక్కటే మార్గం.',
  'checklist.chase_preauth':
    'బీమా కౌంటర్‌లో ముందస్తు అనుమతి గురించి పేరు చెప్పి వెంటపడండి',
  'checklist.chase_preauth.why':
    'చదవకుండా పడి ఉన్న దరఖాస్తే క్యాష్‌లెస్ నగదుగా మారడానికి సాధారణ కారణం. అనుమతి వచ్చిందా అని మాత్రమే కాదు, ఎంత మొత్తం అని అడగండి: బీమా సంస్థలు తరచూ తక్కువ ఆమోదిస్తాయి, తేడా మీదే.',
  'checklist.discharge_summary': 'డిశ్చార్జి సారాంశం తీసుకోండి, సంతకం, ముద్రతో',
  'checklist.discharge_summary.why':
    'ఇది లేకుండా ఏ క్లెయిమూ చెల్లదు. అందులో చికిత్స, రెండు తేదీలు ఉన్నాయో చూడండి.',
  'checklist.itemised_bill':
    'ప్రతి వస్తువు వివరమున్న బిల్లు తీసుకోండి, ఒక్క లైను మొత్తం కాదు',
  'checklist.itemised_bill.why':
    'ఒక్క సంఖ్యను మీ పాలసీతో సరిపోల్చలేరు, బీమా సంస్థ దాన్ని ప్రశ్నిస్తుంది.',
  'checklist.originals': 'అసలు రిపోర్టులు, చీటీలు, రసీదులు తీసుకోండి',
  'checklist.originals.why':
    'అసలువి, జిరాక్సులు కాదు. ఇవి లేకుండా క్లెయిములు తిరస్కరిస్తారు, ఆసుపత్రి రెండో సెట్ ఉంచదు.',
  'checklist.check_non_payables':
    'బీమా ఎప్పుడూ ఇవ్వని వస్తువులు బిల్లులో చూడండి',
  'checklist.check_non_payables.why':
    'గ్లౌజులు, గౌన్లు, రికార్డు ఛార్జీలు IRDAI చెల్లించని జాబితాలో ఉన్నాయి, అవి మీ వైపే. పైన బిల్లు ఫోటో పెట్టండి, మేము వరుసవారీగా చూస్తాం.',
  'checklist.check_deduction': 'దామాషా కోత ఎలా లెక్కించారో చూడండి',
  'checklist.check_deduction.why':
    'ఇది గది, నర్సింగ్, డాక్టర్, సర్జన్, థియేటర్‌కు మాత్రమే. మే 2024 నుంచి ఇది మందులు, పరీక్షలు, ఇంప్లాంట్లు లేదా ఐసీయూను తాకకూడదు. పైన బిల్లు తనిఖీ దాన్ని లెక్కించి ఇస్తుంది.',
  'checklist.post_window':
    'ప్రతి చీటీ, బిల్లు మరో {days} రోజులు జాగ్రత్తగా ఉంచండి',
  'checklist.post_window.why':
    'ఆ కాలంలోని సందర్శనలు, మందులు, పరీక్షలకు క్లెయిమ్ చేయవచ్చు, పారేసిన రసీదు వల్ల ఇవే ఎక్కువగా పోతాయి.',
  'checklist.post_window_until':
    '{until} వరకు ప్రతి చీటీ, బిల్లు జాగ్రత్తగా ఉంచండి',
  'checklist.post_window_until.why':
    'ఆ కాలంలోని సందర్శనలు, మందులు, పరీక్షలకు క్లెయిమ్ చేయవచ్చు, పారేసిన రసీదు వల్ల ఇవే ఎక్కువగా పోతాయి.',
  'checklist.claim_deadline':
    'క్లెయిమ్ పంపడానికి చివరి తేదీ బీమా సంస్థను అడగండి',
  'checklist.claim_deadline.why':
    'రీయింబర్స్‌మెంట్ క్లెయిముకు గడువు ఉంటుంది, సాధారణంగా డిశ్చార్జి నుంచి 15 నుంచి 30 రోజులు. ఆలస్యమైన క్లెయిమ్ తేదీ ఆధారంగానే తిరస్కరిస్తారు.',
  'checklist.final_approval': 'బిల్లుపై సంతకం చేసే ముందు తుది ఆమోదం కోసం ఆగండి',
  'checklist.final_approval.why':
    'తుది ఆమోదం తరచూ ముందస్తు అనుమతికి భిన్నంగా ఉంటుంది, మీరు సంతకం చేసిందే మీరు చెల్లించాల్సింది.',
  'checklist.settlement_letter': 'సెటిల్‌మెంట్ లేఖను బిల్లులతో ఉంచండి',
  'checklist.settlement_letter.why':
    'ఎంత ఇచ్చారు, ఎంత కోశారు అనేది అందులో ఉంటుంది, ప్రతి వాదనా దాని నుంచే జరుగుతుంది.',
  'checklist.check_deductions': 'ప్రతి కోతనూ మీ పాలసీతో సరిపోల్చి చూడండి',
  'checklist.check_deductions.why':
    'మీ పత్రంలోని ఏ షరతుకూ సరిపోని కోతను అడగడం సరైనదే. బీమా సంస్థలు వాటిని సరిచేస్తాయి.',
  'checklist.note_remaining': 'ఈ పాలసీ సంవత్సరంలో ఎంత కవర్ మిగిలిందో రాసుకోండి',
  'checklist.note_remaining.why':
    'రెన్యువల్‌కు ముందు జరిగే ప్రతి అడ్మిషనూ దీనిలోనే ఇమడాలి.',

  // The deduction chain, and what one line of a bill is.
  'waterfall.non_payable': 'ఎప్పుడూ రాని వస్తువులు',
  'waterfall.non_payable.why':
    'గ్లౌజులు, సిరంజీలు, రిజిస్ట్రేషన్ ఎప్పుడూ రావు.',
  'waterfall.non_payable_consumables': 'ఎప్పుడూ రాని వస్తువులు',
  'waterfall.non_payable_consumables.why':
    'గ్లౌజులు, సిరంజీలు, రిజిస్ట్రేషన్ ఎప్పుడూ రావు, వాడకపు సామగ్రికి మీ దగ్గర లేని యాడ్-ఆన్ కావాలి.',
  'waterfall.sublimit': 'ఒక విభాగపు పరిమితి పైన',
  'waterfall.sublimit.why': '{head} పరిమితి {cap}. అంచనా {billed}.',
  'waterfall.room_rent_cap': 'గది మీ కవర్ కంటే ఎక్కువ',
  'waterfall.room_rent_cap.why':
    'మీ గది రోజుకు {rate}, మీ కవర్ {cap}. తేడా మీరు చెల్లిస్తారు.',
  'waterfall.proportionate': 'దామాషా కోత',
  'waterfall.proportionate.why':
    'మీ గది మీ విభాగం కంటే పైన ఉంది, కాబట్టి గదిని బట్టి ఉండే ఖర్చులపై {pct} మాత్రమే వస్తుంది: సర్జన్, థియేటర్, నర్సింగ్. ఐసీయూ, మందులు, పరీక్షలు, ఇంప్లాంట్లు తాకబడవు.',
  'waterfall.procedure_cap': 'ఈ చికిత్స పరిమితి పైన',
  'waterfall.procedure_cap.why':
    'మీ పాలసీ ఈ చికిత్సకు {cap} పరిమితి పెట్టింది.',
  'waterfall.copay': 'మీ కో-పేమెంట్ వాటా',
  'waterfall.copay.why': 'ప్రతి ఆమోదిత క్లెయిములో {pct}% మీరు చెల్లిస్తారు.',
  'waterfall.copay_age': 'మీ కో-పేమెంట్ వాటా',
  'waterfall.copay_age.why':
    'ప్రతి ఆమోదిత క్లెయిములో {pct}% మీరు చెల్లిస్తారు, ఇది {age} ఏళ్లు, ఆపైవారికి ఉన్న కో-పేమెంట్.',
  'waterfall.deductible': 'మీ డిడక్టిబుల్',
  'waterfall.deductible.why':
    'ఇది టాప్-అప్ పాలసీ. ఇది {amount} పైన మాత్రమే ఇస్తుంది, అంత మీది లేదా మరో పాలసీది.',
  'waterfall.sum_insured_exhausted': 'మిగిలిన కవర్ కంటే ఎక్కువ',
  'waterfall.sum_insured_exhausted.why':
    'ఈ సంవత్సరం {remaining} కవర్ మాత్రమే మిగిలింది, క్లెయిమ్ దాని కంటే ఎక్కువ.',
  'waterfall.scheme_package_rate': 'పథకం ప్యాకేజీలో ఉంది',
  'waterfall.scheme_package_rate.why':
    '{scheme} ఈ చికిత్సను నిర్ణీత {rate}కు కొంటుంది. ఆసుపత్రి తన {price} నుంచి తేడాను మీ నుంచి తీసుకోలేదు. సామగ్రి, ఇంప్లాంట్లు, మందులు, పరీక్షలు, భోజనం అన్నీ ప్యాకేజీలోనే.',
  'waterfall.scheme_not_empanelled': 'ఇక్కడ పథకం పనిచేయదు',
  'waterfall.scheme_not_empanelled.why':
    '{hospital} {scheme}లో నమోదు కాలేదు, కాబట్టి పథకం ఇక్కడ ఏమీ ఇవ్వదు.',
  'waterfall.second_policy': 'మీ రెండో పాలసీ చెల్లించింది',
  'waterfall.second_policy.why':
    'మొదటి పాలసీ తర్వాత మిగిలినది మీ రెండో పాలసీ చెల్లించింది.',
  'billnote.nights': '{room}లో {n} రాత్రులు',
  'billnote.icu_days': 'ఇంటెన్సివ్ కేర్‌లో {n} రోజులు',
  'billnote.tier_scaled': 'గది రకాన్ని బట్టి',
  'billnote.non_medical': 'రిజిస్ట్రేషన్, రికార్డులు, అటెండెంట్',
  'bill.lines_at': 'పంక్తులు {lines}',

  // What needs attention now, and what has happened so far.
  'alert.room_rate_conflict': 'మీ గది బిల్లు వేరే ధరతో అవుతోంది',
  'alert.room_rate_conflict.msg':
    'ఈ అడ్మిషన్ రోజుకు {booked}తో నిర్ణయమైంది, నమోదైన ఖర్చులు {observed} అవుతున్నాయి. రెండూ సరైనవి కావు.',
  'alert.room_rate_conflict.do':
    'గది మార్చి ఉంటే ఇది సరైనదే. లేకుంటే ఏ ధర వర్తిస్తుందో బిల్లింగ్ కౌంటర్‌లో అడగండి.',
  'alert.room_over_limit': 'మీ గది మీ కవర్ కంటే ఖరీదైనది',
  'alert.room_over_limit.msg':
    'మీ గది రోజుకు {rate}, మీ కవర్ {cap}. {days} రోజుల్లో అది {excess} గది అద్దె, పైగా సర్జన్, థియేటర్, నర్సింగ్ నుంచి సుమారు {knock_on}.',
  'alert.room_over_limit.do':
    'మీ పరిమితిలోని గది గురించి బీమా కౌంటర్‌లో అడగండి. రేపటి నుంచి తదుపరి కోతలు ఆగుతాయి.',
  'alert.room_over_limit_knock_on': 'మీ గది మీ కవర్ కంటే ఖరీదైనది',
  'alert.room_over_limit_knock_on.msg':
    'మీ గది రోజుకు {rate}, మీ కవర్ {cap}. {days} రోజుల్లో అది {excess} గది అద్దె, పైగా సర్జన్, థియేటర్, నర్సింగ్ నుంచి సుమారు {knock_on}. ఆ రెండో కోత గది కాని ఖర్చులపై పడుతుంది, ఇదే చాలామందికి కనిపించదు.',
  'alert.room_over_limit_knock_on.do':
    'మీ పరిమితిలోని గది గురించి బీమా కౌంటర్‌లో అడగండి. రేపటి నుంచి తదుపరి కోతలు ఆగుతాయి.',
  'alert.sublimit_nearly_used': '{head} పరిమితి దాదాపు అయిపోయింది',
  'alert.sublimit_nearly_used.msg':
    '{head}కు మీ కవర్ {cap}, {spent} బిల్లు అయ్యింది, అంటే {pct}.',
  'alert.sublimit_nearly_used.do':
    'దీని పైన ఉన్నదంతా మీదే. మరిన్ని పరీక్షల ముందు కౌంటర్‌లో అడగండి.',
  'alert.cover_almost_gone': 'మీ కవర్ దాదాపు అయిపోయింది',
  'alert.cover_almost_gone.msg':
    'మీ {total} కవర్‌లో {consumed} బిల్లు అయ్యింది. {remaining} మిగిలింది.',
  'alert.cover_almost_gone.do':
    'డిశ్చార్జి సన్నాహాలు, నేరుగా మీరు ఎంత చెల్లించాలో అడగండి.',
  'alert.cover_on_track_today': 'ఖర్చు మీ కవర్‌ను దాటే దారిలో ఉంది',
  'alert.cover_on_track_today.msg':
    'రోజువారీ ఖర్చులు రోజుకు సుమారు {rate} నడుస్తున్నాయి, ఇప్పటికే బిల్లయిన థియేటర్, ఇంప్లాంట్లు మినహా. ఈ వేగంతో మీ {total} కవర్ ఈరోజే దాటుతుంది.',
  'alert.cover_on_track_today.do':
    'డిశ్చార్జి సమయంలో కాదు, ఇప్పుడే లేవనెత్తాల్సినవి: టాప్-అప్, మరో కవర్, ఆసుపత్రి వాయిదా కౌంటర్ గురించి అడగండి.',
  'alert.cover_on_track_days': 'ఖర్చు మీ కవర్‌ను దాటే దారిలో ఉంది',
  'alert.cover_on_track_days.msg':
    'రోజువారీ ఖర్చులు రోజుకు సుమారు {rate} నడుస్తున్నాయి, ఇప్పటికే బిల్లయిన థియేటర్, ఇంప్లాంట్లు మినహా. ఈ వేగంతో మీ {total} కవర్ సుమారు {days} రోజుల్లో దాటుతుంది.',
  'alert.cover_on_track_days.do':
    'డిశ్చార్జి సమయంలో కాదు, ఇప్పుడే లేవనెత్తాల్సినవి: టాప్-అప్, మరో కవర్, ఆసుపత్రి వాయిదా కౌంటర్ గురించి అడగండి.',
  'alert.cover_on_track_soon': 'ఖర్చు మీ కవర్‌ను దాటే దారిలో ఉంది',
  'alert.cover_on_track_soon.msg':
    'రోజువారీ ఖర్చులు రోజుకు సుమారు {rate} నడుస్తున్నాయి, ఇప్పటికే బిల్లయిన థియేటర్, ఇంప్లాంట్లు మినహా. ఈ వేగంతో మీ {total} కవర్ ఈ అడ్మిషన్‌లోనే దాటుతుంది.',
  'alert.cover_on_track_soon.do':
    'డిశ్చార్జి సమయంలో కాదు, ఇప్పుడే లేవనెత్తాల్సినవి: టాప్-అప్, మరో కవర్, ఆసుపత్రి వాయిదా కౌంటర్ గురించి అడగండి.',
  'alert.cover_most_used': 'మీ కవర్‌లో ఎక్కువ భాగం వాడేశారు',
  'alert.cover_most_used.msg': 'ఈ సంవత్సరం {remaining} కవర్ మిగిలింది.',
  'alert.cover_most_used.do':
    'ముందు మరిన్ని చికిత్సలు అవసరమైతే ఇది గుర్తుంచుకోండి.',
  'alert.non_payable_accumulating': 'మీ పాలసీ ఇవ్వని ఖర్చులు',
  'alert.non_payable_accumulating.msg':
    'ఇప్పటివరకు బిల్లులో {amount} ఏ పాలసీ ఇవ్వని వాటిది: గ్లౌజులు, సిరంజీలు, రిజిస్ట్రేషన్. మిగతాది ఏమైనా, ఇవి మీరే చెల్లిస్తారు.',
  'alert.non_payable_accumulating.do':
    'వీటిని సరిచూసుకోవడానికి వివరమైన బిల్లు అడగండి.',
  'alert.pre_auth_due': 'ముందస్తు అనుమతి పంపాలి',
  'alert.pre_auth_due.msg':
    'క్యాష్‌లెస్‌కు ఆపరేషన్ ముందు బీమా సంస్థ ఆమోదం కావాలి. అది లేకుంటే మీరు ఆసుపత్రికి చెల్లించి తర్వాత క్లెయిమ్ చేయాలి.',
  'alert.pre_auth_due.do': 'దీన్ని ఇప్పుడే పంపమని బీమా కౌంటర్‌కు చెప్పండి.',
  'timeline.start': 'చికిత్స ప్రణాళిక',
  'timeline.back': 'తిరిగి {stage}కు',
  'timeline.skipped': '{stage} (ముందుకు దూకి)',
  'timelinenote.start': '{cover} కవర్.',
  'timelinenote.start_hospital': '{cover} కవర్. {hospital} చూస్తున్నాం.',
  'timelinenote.admitted': '{room}లో చేరిక.',
  'timelinenote.admitted_rate': '{room}లో చేరిక, రోజుకు {rate}.',
  'timelinenote.discharge': 'డిశ్చార్జి పత్రాలు సిద్ధమవుతున్నాయి.',
  'timelinenote.settled': 'మొత్తం బిల్లు {total}.',

  // What stands between this policy and this claim.
  'dur.days': '{n} రోజులు',
  'dur.months': '{n} నెలలు',
  'dur.years': '{n} సంవత్సరాలు',
  'dur.months_days': '{n} నెలలు {d} రోజులు',
  'elig.scheme': 'వేచి ఉండే కాలం లేదు',
  'elig.scheme.detail': 'పథకం కవర్ కార్డు ఇచ్చిన రోజు నుంచే మొదలవుతుంది.',
  'elig.no_start_date': 'మీ పాలసీ ప్రారంభ తేదీని మేము చదవలేకపోయాం',
  'elig.no_start_date.detail':
    'ఇక్కడ వేచి ఉండే కాలం {period} వరకు ఉంటుంది. ప్రారంభ తేదీ లేకుండా అవి ఇంకా వర్తిస్తాయో లేదో చెప్పలేం.',
  'eligask.no_start_date': 'ఈ పాలసీ ఎప్పుడు మొదలైంది?',
  'elig.daycare_excluded': 'కవర్ లేదు: ఇది ఒక రోజు కంటే తక్కువలో ముగుస్తుంది',
  'elig.daycare_excluded.detail':
    '{procedure}కు సాధారణంగా 24 గంటల కంటే తక్కువ పడుతుంది. ఈ పాలసీకి పూర్తి రోజు అడ్మిషన్ కావాలి, డే-కేర్ మినహాయించారు, కాబట్టి కవర్ ఎంత పాతదైనా క్లెయిమ్ తిరస్కరిస్తారు.',
  'elig.daycare_unknown': 'డే-కేర్ కవర్ అవుతుందా చూడండి',
  'elig.daycare_unknown.detail':
    '{procedure}కు సాధారణంగా 24 గంటల కంటే తక్కువ పడుతుంది, సాధారణ కవర్‌కు పూర్తి రోజు కావాలి. ఇక్కడ ఏదీ ఔననీ కాదనీ చెప్పడం లేదు. చేరే ముందు బీమా సంస్థను అడగండి.',
  'elig.initial_accident': 'ప్రమాద గాయంగా కవర్',
  'elig.initial_accident.detail':
    'మొదటి {period} ప్రమాద గాయాన్ని మాత్రమే కవర్ చేస్తాయి, ఇది అదే.',
  'elig.initial_days': '{n} రోజులు కవర్ లేదు',
  'elig.initial_months': 'సుమారు {n} నెలలు కవర్ లేదు',
  'elig.initial_years': 'సుమారు {n} సంవత్సరాలు కవర్ లేదు',
  'elig.initial_days.detail':
    'ఈ పాలసీ {start}న మొదలైంది. మొదటి {period} ఇది ప్రమాద గాయాన్ని మాత్రమే కవర్ చేస్తుంది, కాబట్టి {clears} ముందు ప్రణాళికాబద్ధ అడ్మిషన్ తిరస్కరిస్తారు.',
  'elig.named_days': '{n} రోజులు కవర్ లేదు',
  'elig.named_months': 'సుమారు {n} నెలలు కవర్ లేదు',
  'elig.named_years': 'సుమారు {n} సంవత్సరాలు కవర్ లేదు',
  'elig.named_days.detail':
    'ఈ పాలసీ {named}కు ప్రారంభం నుంచి {period} వేచి ఉంచుతుంది, కాబట్టి {procedure} {clears} నుంచి కవర్.',
  'elig.pre_existing_ask': 'ఇది ముందు నుంచే ఉందా అన్నదానిపై ఆధారపడి ఉంది',
  'elig.pre_existing_ask.detail':
    'పాలసీ మొదలయ్యే ముందు ఉన్న వ్యాధులు {period} వేచి ఉంటాయి, అంటే {clears} వరకు. ప్రారంభం తర్వాత మొదటిసారి కనిపించినది ఇప్పుడే కవర్.',
  'eligask.pre_existing_ask': 'ఈ పాలసీ మొదలయ్యే ముందు ఈ వ్యాధి ఉందా?',
  'elig.pre_existing_days': 'ముందు నుంచీ ఉన్నది: {n} రోజులు కవర్ లేదు',
  'elig.pre_existing_months': 'ముందు నుంచీ ఉన్నది: సుమారు {n} నెలలు కవర్ లేదు',
  'elig.pre_existing_years':
    'ముందు నుంచీ ఉన్నది: సుమారు {n} సంవత్సరాలు కవర్ లేదు',
  'elig.pre_existing_days.detail':
    'పాలసీ మొదలయ్యే ముందు ఉన్న వ్యాధి {clears} నుంచి కవర్ అవుతుంది.',
  'elig.initial_months.detail':
    'ఈ పాలసీ {start}న మొదలైంది. మొదటి {period} ఇది ప్రమాద గాయాన్ని మాత్రమే కవర్ చేస్తుంది, కాబట్టి {clears} ముందు ప్రణాళికాబద్ధ అడ్మిషన్ తిరస్కరిస్తారు.',
  'elig.initial_years.detail':
    'ఈ పాలసీ {start}న మొదలైంది. మొదటి {period} ఇది ప్రమాద గాయాన్ని మాత్రమే కవర్ చేస్తుంది, కాబట్టి {clears} ముందు ప్రణాళికాబద్ధ అడ్మిషన్ తిరస్కరిస్తారు.',
  'elig.named_months.detail':
    'ఈ పాలసీ {named}కు ప్రారంభం నుంచి {period} వేచి ఉంచుతుంది, కాబట్టి {procedure} {clears} నుంచి కవర్.',
  'elig.named_years.detail':
    'ఈ పాలసీ {named}కు ప్రారంభం నుంచి {period} వేచి ఉంచుతుంది, కాబట్టి {procedure} {clears} నుంచి కవర్.',
  'elig.pre_existing_months.detail':
    'పాలసీ మొదలయ్యే ముందు ఉన్న వ్యాధి {clears} నుంచి కవర్ అవుతుంది.',
  'elig.pre_existing_years.detail':
    'పాలసీ మొదలయ్యే ముందు ఉన్న వ్యాధి {clears} నుంచి కవర్ అవుతుంది.',

  // A bill, read and checked against the policy.
  'findkind.uncertain_read': 'చదవడంలో అనిశ్చితి',
  'findkind.optional_item': 'కవర్ లేదు',
  'findkind.subsumed': 'ఇప్పటికే కలిసి ఉంది',
  'findkind.duplicate': 'రెండుసార్లు నమోదు',
  'findkind.line_arithmetic': 'లెక్క సరిపోలడం లేదు',
  'findkind.total_mismatch': 'మొత్తం సరిపోలడం లేదు',
  'findkind.unplaced': 'వర్గీకరించలేకపోయాం',
  'findkind.room_above_cap': 'గది పరిమితి పైన',
  'findkind.proportionate': 'దామాషా కోత',
  'findkind.sublimit': 'విభాగపు పరిమితి',
  'findkind.consumables': 'వాడకపు సామగ్రి',
  'finding.uncertain_read': 'ఈ ఫోటోలోని ప్రతి అంకెనూ మేము చదవలేకపోయాం',
  'finding.uncertain_read.detail':
    'మా పంక్తులు {lines} అవుతున్నాయి, బిల్లు {total} అంటోంది. ఇవి సరిపోవాలి, కాబట్టి కనీసం ఒక అంకె తప్పుగా చదివాం.',
  'finding.uncertain_read.ask':
    'కింది పంక్తులను ముందు కాగితంతో సరిపోల్చండి. నేరుగా, మంచి వెలుతురులో తీసిన ఫోటో లేదా బిల్లింగ్ కౌంటర్ ఇమెయిల్ చేసే PDF కచ్చితంగా చదవబడుతుంది.',
  'finding.uncertain_read_no_total': 'ఈ ఫోటోలోని ప్రతి అంకెనూ మేము చదవలేకపోయాం',
  'finding.uncertain_read_no_total.detail':
    'మా పంక్తులు {lines} అవుతున్నాయి, సరిపోల్చడానికి బిల్లు సొంత మొత్తం మాకు దొరకలేదు.',
  'finding.uncertain_read_no_total.ask':
    'కింది పంక్తులను ముందు కాగితంతో సరిపోల్చండి. నేరుగా, మంచి వెలుతురులో తీసిన ఫోటో లేదా బిల్లింగ్ కౌంటర్ ఇమెయిల్ చేసే PDF కచ్చితంగా చదవబడుతుంది.',
  'finding.listing.optional': '{items}: {amount}',
  'finding.listing.optional.detail': 'ఏ ఆరోగ్య పాలసీలోనూ కవర్ లేదు.',
  'finding.listing.optional.ask':
    'ఇవి మీ వైపువే. పంక్తి సరిగ్గా చదివారా అని మాత్రం చూడండి.',
  'finding.listing.in_room': '{items}: {amount}',
  'finding.listing.in_room.detail': 'గది ఛార్జీలో ఇప్పటికే ఉంది.',
  'finding.listing.in_room.ask':
    'ఇది గది ఛార్జీలో ఎందుకు లేదో అడగండి. ఇది వేరే పంక్తి కాకూడదు.',
  'finding.listing.in_procedure': '{items}: {amount}',
  'finding.listing.in_procedure.detail': 'ఆపరేషన్ ఛార్జీలో ఇప్పటికే ఉంది.',
  'finding.listing.in_procedure.ask':
    'ఇది ఆపరేషన్ ఛార్జీలో ఎందుకు లేదో అడగండి. ఇది వేరే పంక్తి కాకూడదు.',
  'finding.listing.in_treatment': '{items}: {amount}',
  'finding.listing.in_treatment.detail': 'చికిత్స ఖర్చులో ఇప్పటికే ఉంది.',
  'finding.listing.in_treatment.ask':
    'ఇది చికిత్స ఖర్చులో ఎందుకు లేదో అడగండి. ఇది వేరే పంక్తి కాకూడదు.',
  'finding.duplicate': '{item} {n} సార్లు వచ్చింది, ప్రతిసారి {amount}',
  'finding.duplicate.detail': 'పంక్తులు {lines}.',
  'finding.duplicate.ask':
    'ఇది రెండుసార్లు నమోదైందా అని అడగండి. రెండు వేర్వేరు రోజుల అదే ఖర్చు సాధారణమే, కాబట్టి జవాబు అవును కావచ్చు, కానీ అడగడానికి ఏమీ పోదు.',
  'finding.line_arithmetic_over':
    '{item}: {qty} × {rate} వల్ల {expected} అవుతుంది, {billed} కాదు',
  'finding.line_arithmetic_over.detail':
    'గుణించగా వచ్చేదాని కంటే {difference} ఎక్కువ.',
  'finding.line_arithmetic_over.ask':
    'మూడింటిలో ఏ అంకె సరైనదో అడగండి. తప్పు ధరకు వేసిన పరిమాణమే అత్యంత సాధారణ బిల్లింగ్ పొరపాటు.',
  'finding.line_arithmetic_under':
    '{item}: {qty} × {rate} వల్ల {expected} అవుతుంది, {billed} కాదు',
  'finding.line_arithmetic_under.detail':
    'గుణించగా వచ్చేదాని కంటే {difference} తక్కువ.',
  'finding.line_arithmetic_under.ask':
    'మూడింటిలో ఏ అంకె సరైనదో అడగండి. తప్పు ధరకు వేసిన పరిమాణమే అత్యంత సాధారణ బిల్లింగ్ పొరపాటు.',
  'finding.total_mismatch':
    'పంక్తులు {lines} అవుతున్నాయి, బిల్లు {total} అంటోంది',
  'finding.total_mismatch.detail': '{difference} తేడా.',
  'finding.total_mismatch.ask':
    'మొత్తాన్ని మీ ముందే కూడమని చెప్పండి. ఏదో ఒక పంక్తి తప్పిపోయింది లేదా మొత్తం తప్పు, సంతకం ముందు రెండూ పరిష్కరించుకోవడం మంచిది.',
  'finding.unplaced': '{n} పంక్తులను వర్గీకరించలేకపోయాం, {amount}',
  'finding.unplaced.detail': '{items}.',
  'finding.unplaced.ask':
    'ఊహించే బదులు వీటిని కింది లెక్క నుంచి తీసేశాం, కాబట్టి ఆ అంకెలు పూర్తి బిల్లు కంటే ఇంత తక్కువ.',
  'finding.consumables': 'ఈ బిల్లులో వాడకపు సామగ్రి: {amount}',
  'finding.consumables.detail':
    'యాడ్-ఆన్ తీసుకోకుంటే పాలసీలు వాడకపు సామగ్రిని మినహాయిస్తాయి, కాబట్టి మిగతాది ఏమైనా ఈ భాగం మీదే.',
  'finding.consumables.ask':
    'పంక్తి నిజంగా వాడకపు సామగ్రేనా, మందులు కాదా చూడండి, ఎందుకంటే మందులను మీ పాలసీ ఇస్తుంది.',
  'finding.room_rent_cap': 'గది మీ కవర్ కంటే ఎక్కువ: {amount}',
  'finding.room_rent_cap.detail':
    'మీ గది రోజుకు {rate}, మీ కవర్ {cap}. తేడా మీరు చెల్లిస్తారు.',
  'finding.room_rent_cap.ask':
    'ఇది బిల్లులో లేదు, కౌంటర్ దీన్ని లేవనెత్తదు. బీమా సంస్థ సెటిల్‌మెంట్ సమయంలో కోసేస్తుంది, కాబట్టి దీన్ని మీరే సమకూర్చుకోవాలి.',
  'finding.proportionate': 'దామాషా కోత: {amount}',
  'finding.proportionate.detail':
    'మీ గది మీ విభాగం కంటే పైన ఉంది, కాబట్టి గదిని బట్టి ఉండే ఖర్చులపై {pct} మాత్రమే వస్తుంది: సర్జన్, థియేటర్, నర్సింగ్. ఐసీయూ, మందులు, పరీక్షలు, ఇంప్లాంట్లు తాకబడవు.',
  'finding.proportionate.ask':
    'ఇది ఎలా లెక్కించారో చూడండి. మే 2024 నుంచి ఇది గదితో ముడిపడిన ఖర్చులకు మాత్రమే: గది, నర్సింగ్, డాక్టర్, సర్జన్, థియేటర్. మందులు, పరీక్షలు, ఇంప్లాంట్లు లేదా ఐసీయూ కూడా కోసి ఉంటే ప్రశ్నించండి.',
  'finding.sublimit': 'విభాగపు పరిమితి పైన: {amount}',
  'finding.sublimit.detail': '{head} పరిమితి {cap}. అంచనా {billed}.',
  'finding.sublimit.ask':
    'పరిమితి, అది దేనిపై లెక్కిస్తారో బీమా సంస్థ నుంచి నిర్ధారించుకోండి. దాని పైన మిగిలినది మీదే.',

  // Warnings, notes, and how one hospital was chosen over another.
  'warn.proportionate':
    'ఈ గది గది తేడాతో పాటు సుమారు {amount} దామాషా కోతనూ తెస్తుంది.',
  'warn.room_category':
    'మీ కవర్ {covered}కు, మీరు {chosen} ఎంచుకున్నారు. సంబంధిత ఖర్చులు కోసే అవకాశం ఉంది. బీమా కౌంటర్‌లో అడగండి.',
  'warn.cover_used_up':
    'ఈ చికిత్స మీ దగ్గర మిగిలిన {remaining}ను పూర్తిగా ఖర్చు చేస్తుంది.',
  'warn.not_cashless':
    'మీకు ఇది క్యాష్‌లెస్ ఆసుపత్రి కాదు. ఇక్కడ పూర్తి {total} మీరు చెల్లించి, తర్వాత {payable} తిరిగి అడుగుతారు.',
  'warn.scheme_cover_short':
    'ఈ సంవత్సరం మీ {scheme} కవర్ {remaining} మాత్రమే మిగిలింది, ఈ చికిత్స {rate}. తేడాను ఆసుపత్రి మిమ్మల్ని అడుగుతుంది.',
  'warn.scheme_upgrade':
    'మీరు {chosen} ఎంచుకున్నారు; {scheme}లో {covered} వస్తుంది. పైభాగం మీది, మొత్తం అడ్మిషన్‌కు సుమారు {amount}. మిగతా ఏదీ కోయబడదు.',
  'warn.scheme_unusable':
    '{scheme} ఇక్కడ పనిచేయదు, తర్వాత అడగడానికీ ఏమీ లేదు: అది నమోదైన ఆసుపత్రులకే ఇస్తుంది. పూర్తి {total} మీదే అవుతుంది. {scheme} స్వీకరించే ఆసుపత్రిని ఎంచుకోండి.',
  'warn.scheme_unusable_reimbursable':
    '{scheme} ఇక్కడ పనిచేయదు. కొన్ని ఖర్చులు తిరిగి రావచ్చు, కానీ ముందుగా అనుమతి తీసుకుంటేనే. చేరే ముందు నిర్ధారించుకోండి.',
  'note.consumables_covered': 'మీ పాలసీ వాడకపు సామగ్రిని కూడా ఇస్తుంది.',
  'note.copay_not_applicable':
    '{pct}% కో-పేమెంట్ {age} ఏళ్ల నుంచి మొదలవుతుంది, కాబట్టి ఇక్కడ వర్తించదు.',
  'note.restore':
    'ఈ పాలసీ ఏడాదికి ఒకసారి కవర్‌ను తిరిగి నింపుతుంది, తదుపరి అడ్మిషన్‌కు {amount} వస్తుంది. ఇదే అడ్మిషన్‌కు వాడొచ్చా అని బీమా సంస్థను అడగండి; పాలసీలు వేరువేరుగా ఉంటాయి.',
  'note.which_insurer_first':
    'IRDAI నిబంధన ప్రకారం ముందు ఏ బీమా సంస్థ దగ్గరకు వెళ్లాలో మీరే నిర్ణయిస్తారు. రెండింటికీ ఒకదాని గురించి మరొకటి చెప్పండి: రెండో పాలసీ దాచి పరిష్కారమైన క్లెయిమ్ మళ్లీ తెరవవచ్చు.',
  'note.scheme_room_free': '{room} ఉచితంగా ఉంది.',
  'note.scheme_nothing_to_pay':
    'ఇక్కడ ఏమీ చెల్లించనవసరం లేదు, తర్వాత అడగడానికీ ఏమీ లేదు.',
  'note.scheme_window_after':
    'డిశ్చార్జి తర్వాత {after} రోజుల చికిత్స ఇందులో ఉంది.',
  'note.scheme_window_both':
    'డిశ్చార్జి తర్వాత {after} రోజులు, చేరిక ముందు {before} రోజుల చికిత్స ఇందులో ఉంది.',
  'order.forced':
    'ముందు {lead} నుంచి క్లెయిమ్ చేయండి, తర్వాత మిగతాదానికి {second}. ఇదే వరుస సరైనది: టాప్-అప్ మరో పాలసీ ముందు కవర్ చేసే పరిమితి పైన మాత్రమే ఇస్తుంది.',
  'order.cheaper':
    'ముందు {lead} నుంచి క్లెయిమ్ చేయండి, తర్వాత మిగతాదానికి {second}. తిరగబడిన వరుసలో మీరు {this} బదులు {other} చెల్లించాల్సి వచ్చేది.',
  'order.same':
    'ముందు {lead} నుంచి క్లెయిమ్ చేయండి, తర్వాత మిగతాదానికి {second}. ఇక్కడ రెండు వరుసలూ ఒకే మొత్తానికి వస్తాయి.',
  'reason.cheapest': 'దొరికిన ఎంపికల్లో అత్యంత చౌక.',
  'reason.nearest': 'అత్యంత దగ్గర, సుమారు {n} నిమిషాలు.',
  'reason.best_equipped': 'దొరికిన ఎంపికల్లో అత్యుత్తమ సౌకర్యం.',
  'reason.cashless': 'క్యాష్‌లెస్: బీమా సంస్థ నేరుగా ఆసుపత్రికి చెల్లిస్తుంది.',
  'reason.accredited': '{accreditation}.',
  'reason.balanced':
    'ఖర్చు, దూరం మధ్య సమతుల్యత: మీకు {amount}, {km} కిమీ దూరం.',
  'tradeoff.pay_first':
    'ఇక్కడ మీరు {amount} చెల్లించి తర్వాత తిరిగి అడుగుతారు.',
  'tradeoff.costlier': 'దొరికిన అత్యంత చౌకదాని కంటే {amount} ఎక్కువ.',
  'tradeoff.further': '{km} కిమీ దూరం, అత్యంత దగ్గరిదాని కంటే అవతల.',
  'counterfactual.saving':
    'ఇక్కడ {room} తీసుకుంటే సుమారు {amount} ఆదా అయ్యేది.',
  'counterfactual.within_cap':
    'ఇక్కడ {room} తీసుకుంటే సుమారు {amount} ఆదా అయ్యేది, ఎందుకంటే అది మీకు కవర్ ఉన్న రోజుకు {cap} లోపలే ఉంటుంది.',
  'search.no_treatment': 'ముందు చికిత్సను ఎంచుకోండి.',
  'search.none': 'మాకు సరైన ఆసుపత్రి దొరకలేదు.',
  'search.none_offering': 'ఇక్కడ ఏ ఆసుపత్రీ {procedure} చేయదు.',
  'search.no_estimate':
    'ఆసుపత్రులు దొరికాయి, కానీ వాటి ఖర్చు అంచనా వేయలేకపోయాం.',
  'search.starved':
    '{procedure} కోసం మీ అన్ని షరతులకూ ఏ ఆసుపత్రీ సరిపోలేదు. సాధారణ కారణం {reason}, {n} ఆసుపత్రుల్లో. వెతికే పరిధిని పెంచి చూడండి.',
  'search.found': '{n} ఎంపికలు దొరికాయి. మీ అత్యల్ప అంచనా {amount}.',
  'search.found_relaxed':
    '{n} ఎంపికలు దొరికాయి. మీ అత్యల్ప అంచనా {amount}. వీటిని పొందడానికి మీ కొన్ని షరతులను సడలించాల్సి వచ్చింది.',
  'advice.too_far': 'వెతికే పరిధిని పెంచితే ఎక్కువ ఆసుపత్రులు వస్తాయి.',
  'advice.procedure_unavailable':
    'దగ్గరలో తక్కువ ఆసుపత్రులు ఈ చికిత్స చేస్తాయి. పరిధిని పెంచడమే ఎక్కువ ఉపయోగం.',
  'advice.specialty_unavailable':
    'ఈ విభాగం మీ చుట్టుపక్కల తక్కువ. పరిధిని పెంచి చూడండి.',
  'advice.not_cashless':
    'చుట్టుపక్కల ఎక్కువ ఆసుపత్రులు మీ క్యాష్‌లెస్ నెట్‌వర్క్ బయట ఉన్నాయి. వాటిని చేర్చడమంటే ముందు చెల్లించి తర్వాత తిరిగి అడగడం.',
  'advice.no_bed_available':
    'అడ్డంకి పడకలది, మీ కవర్‌ది కాదు. బయలుదేరే ముందు కింది ఆసుపత్రులకు ఫోన్ చేయడం మంచిది.',
  'advice.no_eligible_room':
    'మీ గది అర్హత చుట్టుపక్కల ఎక్కువ ఆసుపత్రులను తొలగిస్తోంది. పై విభాగాన్ని ఒప్పుకుంటే మరిన్ని ఎంపికలు తెరుచుకుంటాయి, కానీ ఖర్చుతో.',
  'relax.wider_radius': 'మేము విస్తృత పరిధిలో వెతికాం.',
  'relax.wider_radius.also': 'మీరు మరింత దూరం వెళ్లాలి.',
  'relax.room_category': 'మీ అర్హత కంటే పైన ఉన్న గదులనూ చేర్చాం.',
  'relax.room_category.also':
    'అర్హత కంటే పైన ఉన్న గది మిగతా ఖర్చులపై వచ్చే మొత్తాన్ని కూడా తగ్గిస్తుంది. కింద చూపిన ఖర్చు దాన్ని ఇప్పటికే కలిపింది.',
  'relax.bed_availability': 'ఇప్పుడు పడక ఖాళీ లేని ఆసుపత్రులనూ చేర్చాం.',
  'relax.bed_availability.also':
    'ముందు ఫోన్ చేయండి: చేరుకున్నప్పుడు పడక ఖాళీగా ఉండకపోవచ్చు.',
  'relax.non_network': 'మీ క్యాష్‌లెస్ నెట్‌వర్క్ బయటి ఆసుపత్రులనూ చేర్చాం.',
  'relax.non_network.also':
    'అక్కడ పూర్తి బిల్లు మీరు చెల్లించి తర్వాత తిరిగి అడుగుతారు, అంటే పూర్తి మొత్తం ముందే సమకూర్చుకోవాలి.',
  'doc.unreadable':
    'ఈ ఫైలు నుంచి మాకు తగినంత చదవలేకపోయాం. స్పష్టమైన ఫోటో తీయండి, లేదా మీ వివరాలు మీరే టైప్ చేయండి.',
  'doc.hard_to_read':
    'ఇది చదవడం కష్టమైంది, కొన్ని వివరాలు తప్పు కావచ్చు. అంకెలు సరిచూసుకోండి.',
  'doc.unreadable_pages': 'మేము పేజీ {pages} చదవలేకపోయాం.',
  'doc.no_schedule':
    'ఇక్కడ పాలసీ షెడ్యూలు దొరకలేదు. చూపిన అంకెలు మీవి కాకుండా సాధారణ షరతులు కావచ్చు.',
}
