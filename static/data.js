/*
  ==========================================================================
  LITERA — შიგთავსის მონაცემთა ფაილი
  ==========================================================================
  როგორ დავამატოთ კონტენტი:

  1) ყოველ ნაწარმოებს აქვს "parts" (თავები/ნაწილები). თითოეულ ნაწილს
     აქვს ცარიელი "summary" ველი — ჩაწერეთ იქ მოკლე შინაარსი (უბრალო
     ტექსტი ან მარტივი HTML, მაგ. <p>...</p>).

  2) "characters" — პერსონაჟების პროფილები. დაამატეთ ობიექტები ასეთი
     ფორმით: { name: "სახელი", role: "როლი/დახასიათება ერთ სიტყვაში",
     description: "სრული აღწერა..." }

  3) "essayThemes" — საკითხავი/საშეფასებელი თემები ესეებისთვის.
     დაამატეთ უბრალო სტრიქონები მასივში: "თემის სათაური..."

  ცარიელი ველები საიტზე გამოჩნდება, როგორც "ჯერ არ არის დამატებული" —
  ეს ნორმალურია, უბრალოდ შეავსეთ ეს ფაილი და განაახლეთ გვერდი.
  ==========================================================================
*/

const LITERA_CATEGORIES = [
  {
    id: "hagiography",
    title: "ძველი ქართული მწერლობა",
    subtitle: "აგიოგრაფია — წამებისა და ღვაწლის თხზულებანი",
    emblem: "cross"
  },
  {
    id: "rustaveli",
    title: "შოთა რუსთაველი",
    subtitle: "„ვეფხისტყაოსანი“ — ქართული სულის სავანე",
    emblem: "tiger"
  },
  {
    id: "transitional",
    title: "XVII–XVIII საუკუნეები",
    subtitle: "სიბრძნისა და თავგადასავლის ხანა",
    emblem: "quill"
  },
  {
    id: "romanticism",
    title: "რომანტიზმი",
    subtitle: "XIX საუკუნის პირველი ნახევარი",
    emblem: "star"
  },
  {
    id: "realism",
    title: "რეალიზმი",
    subtitle: "XIX საუკუნის მეორე ნახევარი",
    emblem: "lamp"
  },
  {
    id: "xx-prose",
    title: "XX საუკუნის პროზა",
    subtitle: "რომანი და მოთხრობა ახალ ეპოქაში",
    emblem: "tower"
  },
  {
    id: "symbolism",
    title: "სიმბოლიზმი და მოდერნიზმი",
    subtitle: "„ცისფერყანწელები“ და თანამოაზრენი",
    emblem: "moon"
  },
  {
    id: "modern",
    title: "თანამედროვე მწერლობა",
    subtitle: "XX საუკუნის მეორე ნახევარი",
    emblem: "leaf"
  }
];

/*
  emptyParts([...])  — შუალედური დამხმარე ფუნქცია: ქმნის ნაწილების მასივს
  მხოლოდ სათაურებით, ცარიელი შინაარსით.
*/
function emptyParts(titles) {
  return titles.map((t) => ({ title: t, summary: "" }));
}

const LITERA_AUTHORS = [
  {
    id: "xucesi",
    name: "იაკობ ხუცესი",
    category: "hagiography",
    works: [
      {
        slug: "shushanikis-tsameba",
        title: "შუშანიკის წამება",
        type: "ჰაგიოგრაფია",
        note: "საკლასო შემოკლებული ვარიანტი",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "sabanisdze",
    name: "იოვანე საბანისძე",
    category: "hagiography",
    works: [
      {
        slug: "abo-tbilelis-tsameba",
        title: "აბო თბილელის წამება",
        type: "ჰაგიოგრაფია",
        note: "საკლასო შემოკლებული ვარიანტი",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "merchule",
    name: "გიორგი მერჩულე",
    category: "hagiography",
    works: [
      {
        slug: "grigol-khandztelis-tskhovreba",
        title: "გრიგოლ ხანძთელის ცხოვრება",
        type: "ჰაგიოგრაფია",
        note: "საკლასო შემოკლებული ვარიანტი",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "rustaveli",
    name: "შოთა რუსთაველი",
    category: "rustaveli",
    works: [
      {
        slug: "vepkhistkaosani",
        title: "ვეფხისტყაოსანი",
        type: "პოემა",
        note: "საკლასო გამოცემა, ნ. ნათაძის რედაქციით",
        parts: emptyParts(["დასაწყისიდან", "თარიელის თათბირამდე", "დასასრული"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "saba-orbeliani",
    name: "სულხან-საბა ორბელიანი",
    category: "transitional",
    works: [
      {
        slug: "sibrdzne-sitsruisa",
        title: "სიბრძნე-სიცრუისა",
        type: "იგავურ-ალეგორიული კრებული",
        note: "",
        parts: emptyParts([
          "მემკვიდრის აღზრდის ამბავი",
          "ლეონის თავგადასავალი",
          "იგავი: მეფე ხორასნისა",
          "იგავი: ძუნწი დიდვაჭარი",
          "იგავი: უგუნური მცურავი",
          "იგავი: სამნი ბრმანი",
          "იგავი: მეფუნდუკე და დიდვაჭარი"
        ]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "guramishvili",
    name: "დავით გურამიშვილი",
    category: "transitional",
    works: [
      {
        slug: "davitiani",
        title: "დავითიანი",
        type: "პოემათა კრებული",
        note: "",
        parts: emptyParts([
          "სწავლა მოსწავლეთა",
          "ქართველთ უფალთა მეგვარტომობის იგავი",
          "მოთქმა ხმითა თავ-ბოლო ერთი",
          "ქართველთა და კახთაგან თავიანთ უფალთად შეორგულება",
          "საწყაულის მოწყვა ღვთისაგან",
          "დავით გურამიშვილის ლეკთაგან დატყვევება",
          "ოდეს დატყვევებულმან ურჯულოს ქვეყანას საყვარლის სახე და სურათი ვეღარა ნახა — ამისი მოთქმა დავითისაგან",
          "ტყვეობითგან გაპარვა დავითისა",
          "შველა ღვთისაგან დავითისა — ტყვეობიდან გამოსვლა რუსეთში",
          "დავით გურამიშვილისაგან საწუთროს სოფლის სამდურავი"
        ]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "al-chavchavadze",
    name: "ალექსანდრე ჭავჭავაძე",
    category: "romanticism",
    works: [
      {
        slug: "gogcha",
        title: "გოგჩა",
        type: "ლექსი",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "gr-orbeliani",
    name: "გრიგოლ ორბელიანი",
    category: "romanticism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts([
          "თამარ მეფის სახე ბეთანიის ეკლესიაში",
          "საღამო გამოსალმებისა",
          "პასუხი შვილთა"
        ]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "baratashvili",
    name: "ნიკოლოზ ბარათაშვილი",
    category: "romanticism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts([
          "არ უკიჟინო, სატრფოო",
          "მერანი",
          "ცისა ფერს",
          "ფიქრნი მტკვრის პირას",
          "შემოღამება მთაწმინდაზედ",
          "ხმა იდუმალი",
          "სულო ბოროტო",
          "ვპოვე ტაძარი"
        ]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "bedi-qartlisa",
        title: "ბედი ქართლისა",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "ilia",
    name: "ილია ჭავჭავაძე",
    category: "realism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts(["ბედნიერი ერი", "პასუხის პასუხი", "ჩემო კალამო"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "gandegili",
        title: "განდეგილი",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "achrdili",
        title: "აჩრდილი",
        type: "პოემა",
        note: "VII თავი",
        parts: emptyParts(["VII თავი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "katsia-adamiani",
        title: "კაცია-ადამიანი?!",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "mgzavris-tserilebi",
        title: "მგზავრის წერილები",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "otaraant-qvrivi",
        title: "ოთარაანთ ქვრივი",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "ra-gitkhrat",
        title: "რა გითხრათ? რით გაგახაროთ?",
        type: "პუბლიცისტური სტატია",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "akaki",
    name: "აკაკი წერეთელი",
    category: "realism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts(["აღმართ-აღმართ", "განთიადი", "სულიკო", "ქებათა ქება"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "tornike-eristavi",
        title: "თორნიკე ერისთავი",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "gamzrdeli",
        title: "გამზრდელი",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "kazbegi",
    name: "ალექსანდრე ყაზბეგი",
    category: "realism",
    works: [
      {
        slug: "khevisberi-gocha",
        title: "ხევისბერი გოჩა",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "vazha-pshavela",
    name: "ვაჟა-ფშაველა",
    category: "realism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts(["ჩემი ვედრება", "რამ შემქმნა ადამიანად", "კაი ყმა", "იას უთხარით ტურფასა"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "aluda-qetelauri",
        title: "ალუდა ქეთელაური",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "bakhtrioni",
        title: "ბახტრიონი",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "stumar-maspindzeli",
        title: "სტუმარ-მასპინძელი",
        type: "პოემა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "amodis-natdeba",
        title: "ამოდის, ნათდება",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      },
      {
        slug: "kosmopolitizmi-da-patriotizmi",
        title: "კოსმოპოლიტიზმი და პატრიოტიზმი",
        type: "პუბლიცისტური წერილი",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "kldiashvili",
    name: "დავით კლდიაშვილი",
    category: "realism",
    works: [
      {
        slug: "samanishvilis-dedinatsvali",
        title: "სამანიშვილის დედინაცვალი",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "lortkipanidze",
    name: "ნიკო ლორთქიფანიძე",
    category: "realism",
    works: [
      {
        slug: "shelotsva-radiot",
        title: "შელოცვა რადიოთი",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "gamsakhurdia",
    name: "კონსტანტინე გამსახურდია",
    category: "xx-prose",
    works: [
      {
        slug: "didostatis-marjvena",
        title: "დიდოსტატის მარჯვენა",
        type: "რომანი",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "javakhishvili",
    name: "მიხეილ ჯავახიშვილი",
    category: "xx-prose",
    works: [
      {
        slug: "jaqos-khiznebi",
        title: "ჯაყოს ხიზნები",
        type: "რომანი",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "qiacheli",
    name: "ლეო ქიაჩელი",
    category: "xx-prose",
    works: [
      {
        slug: "haki-adzba",
        title: "ჰაკი აძბა",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "kakabadze",
    name: "პოლიკარპე კაკაბაძე",
    category: "xx-prose",
    works: [
      {
        slug: "yvaryvare-tutaberi",
        title: "ყვარყვარე თუთაბერი",
        type: "პიესა",
        note: "I და IV მოქმედებები",
        parts: emptyParts(["I მოქმედება", "IV მოქმედება"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "galaktion",
    name: "გალაკტიონ ტაბიძე",
    category: "symbolism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts([
          "ქებათა ქება ნიკორწმინდას",
          "თოვლი",
          "მე და ღამე",
          "მთაწმინდის მთვარე",
          "სილაჟვარდე ანუ ვარდი სილაში",
          "შერიგება",
          "მშობლიური ეფემერა"
        ]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "titsian",
    name: "ტიციან ტაბიძე",
    category: "symbolism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts(["ლექსი მეწყერი", "ანანურთან"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "iashvili",
    name: "პაოლო იაშვილი",
    category: "symbolism",
    works: [
      {
        slug: "poezia",
        title: "პოეზია",
        type: "ლექსი",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "leonidze",
    name: "გიორგი ლეონიძე",
    category: "symbolism",
    works: [
      {
        slug: "leqsebi",
        title: "ლექსები",
        type: "ლირიკა",
        note: "",
        parts: emptyParts(["ნინოწმინდის ღამე", "ყივჩაღის ფაემანი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "rcheulishvili",
    name: "გურამ რჩეულიშვილი",
    category: "modern",
    works: [
      {
        slug: "alaverdoba",
        title: "ალავერდობა",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "kalandadze",
    name: "ანა კალანდაძე",
    category: "modern",
    works: [
      {
        slug: "mkvdarta-mze-var",
        title: "მკვდართა მზე ვარ",
        type: "ლექსი",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "qarchkhadze",
    name: "ჯემალ ქარჩხაძე",
    category: "modern",
    works: [
      {
        slug: "igi",
        title: "იგი",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  },
  {
    id: "dochanashvili",
    name: "გურამ დოჩანაშვილი",
    category: "modern",
    works: [
      {
        slug: "katsi-romelsats-literatura",
        title: "კაცი, რომელსაც ლიტერატურა ძლიერ უყვარდა",
        type: "მოთხრობა",
        note: "",
        parts: emptyParts(["მთლიანი ტექსტი"]),
        characters: [],
        essayThemes: []
      }
    ]
  }
];
