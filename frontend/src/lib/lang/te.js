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
