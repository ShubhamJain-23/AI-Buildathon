import os
import sys
from quotations_builder import build_quotation_pdf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_quotations")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common Client Details
CLIENT_AITM = {
    "org_name": "Apex Institute of Technology & Management",
    "address": "Campus Road, Sector 5, Sitapura Institutional Area, Jaipur, Rajasthan - 302022",
    "gstin": "08AAATA8899K1Z5",
    "ship_to": "Apex Institute of Technology & Management (Central Receiving Store)",
    "ship_location": "Gate No. 2, Stores & Inventory Wing, Sitapura Campus, Jaipur - 302022"
}

# -------------------------------------------------------------
# 1. IT DEPARTMENT QUOTATIONS
# -------------------------------------------------------------

# 1.1 TechNova Peripherals Pvt. Ltd.
q1_it_technova = {
    "primary_color": "#1E3A8A", # Deep Navy Blue
    "secondary_color": "#DBEAFE",
    "company": {
        "name": "TechNova Peripherals Private Limited",
        "tagline": "Enterprise Audio-Visual & Workplace IT Hardware Systems",
        "cin": "U72900RJ2018PTC061234",
        "gstin": "08AABCT1234F1Z8",
        "pan": "AABCT1234F",
        "udyam": "UDYAM-RJ-14-0023451",
        "address": "Plot 42-45, Malviya Industrial Area, Near Calgiri Marg, Jaipur, Rajasthan - 302017",
        "email": "sales@technovaperipherals.com",
        "phone": "+91 141 278 9100 / +91 98290 12345",
        "web": "www.technovaperipherals.com",
        "bank": {
            "holder": "TechNova Peripherals Private Limited",
            "name": "HDFC Bank Ltd",
            "account": "50200034189211",
            "ifsc": "HDFC0000280",
            "branch": "Malviya Nagar, Jaipur"
        },
        "signatory_title": "Director - Enterprise Sales & Institutional Alliances"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Information Technology & Network Services",
        "contact_person": "Head of IT Infrastructure & Procurement Committee"
    },
    "meta": {
        "quote_no": "TNP/2026-27/QT-0891",
        "quote_date": "10-Nov-2026",
        "validity": "30 Days",
        "valid_till": "10-Dec-2026",
        "rfq_ref": "AITM/IT/WEB-CAM/2026/044",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "Supply of 20 Enterprise Webcams & Accessories for Conference & Hybrid Workstations",
    "items": [
        {
            "name": "Logitech C925e Enterprise Business HD Webcam",
            "specs": "Full HD 1080p @ 30fps video streaming, H.264 UVC 1.5 compression, 78° diagonal field of view, Autofocus, RightLight 2 low-light optimization, Dual integrated omni-directional stereo microphones with noise-cancellation, Integrated internal privacy sliding shutter, USB 2.0/3.0 Type-A Plug & Play, Certified for Microsoft Teams, Zoom, Google Meet.",
            "hsn": "85258900",
            "qty": 20,
            "unit": "Units",
            "rate": 6850.00
        },
        {
            "name": "Mini Adjustable Tabletop Tripods (Heavy Duty Aluminum)",
            "specs": "Extendable 6 to 9 inches, 360-degree panoramic ball head mount, standard 1/4-inch universal mounting screw, anti-skid rubber feet for desk stabilization.",
            "hsn": "90069100",
            "qty": 20,
            "unit": "Units",
            "rate": 450.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees One Lakh Seventy-Two Thousand Two Hundred Eighty Only",
    "terms": [
        "<b>Delivery:</b> Delivery within 3 to 5 business days upon receipt of confirmed Purchase Order.",
        "<b>Warranty:</b> 3 Years comprehensive manufacturer replacement warranty with on-site pickup & swap facility.",
        "<b>Payment Terms:</b> 100% payment within 15 calendar days following delivery, physical inspection, and verification at the Central Store.",
        "<b>Transit & Freight:</b> Doorstep delivery included; transit insurance covered by TechNova until physical receipt.",
        "<b>Jurisdiction:</b> Disputes subject strictly to the exclusive jurisdiction of the competent courts in Jaipur, Rajasthan."
    ]
}

# 1.2 NexGen Infotech Solutions LLP
q2_it_nexgen = {
    "primary_color": "#0F766E", # Deep Teal
    "secondary_color": "#CCFBF1",
    "company": {
        "name": "NexGen Infotech Solutions LLP",
        "tagline": "Smart Computing, Unified Communications & Enterprise Audio-Visual",
        "cin": "LLPIN: AAT-9842",
        "gstin": "08BBDNI9823K1ZX",
        "pan": "BBDNI9823K",
        "udyam": "UDYAM-RJ-14-0089124",
        "address": "Suite 304-306, Apex Mall, Tonk Road, Jaipur, Rajasthan - 302015",
        "email": "enterprise@nexgeninfotech.in",
        "phone": "+91 141 405 6789 / +91 94140 55678",
        "web": "www.nexgeninfotech.in",
        "bank": {
            "holder": "NexGen Infotech Solutions LLP",
            "name": "ICICI Bank Ltd",
            "account": "001205018923",
            "ifsc": "ICIC0000012",
            "branch": "Tonk Road, Jaipur"
        },
        "signatory_title": "Designated Partner - IT Solutions"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Information Technology & System Administration",
        "contact_person": "Chief Technology Officer / IT Procurement Manager"
    },
    "meta": {
        "quote_no": "NGIS/HW/NOV-442",
        "quote_date": "12-Nov-2026",
        "validity": "21 Days",
        "valid_till": "03-Dec-2026",
        "rfq_ref": "AITM/IT/WEB-CAM/2026/044",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "Supply of 20 AnkerWork 2K Quad-HD AI Webcams for Executive & Developer Stations",
    "items": [
        {
            "name": "AnkerWork C310 2K Quad-HD High-Definition AI Webcam",
            "specs": "2560x1440p @ 30fps / 1080p @ 60fps, Ultra-clear 1/2.7” CMOS sensor, AI-powered Auto-Framing and smart light adjustment, Dual high-sensitivity microphones with VoiceFocus noise cancellation, Adjustable field of view (65°, 78°, 95°), Built-in physical privacy shutter, Integrated multi-angle monitor mount clamp.",
            "hsn": "85258900",
            "qty": 20,
            "unit": "Units",
            "rate": 7400.00
        },
        {
            "name": "Braided USB-C to USB-A 3.0 Adapter & Cable Retention Kit",
            "specs": "High-durability 10Gbps rated aluminum alloy USB-C female to USB-A male converters + 3M cable clips. Supplied as complimentary educational promotion pack.",
            "hsn": "85444299",
            "qty": 20,
            "unit": "Packs",
            "rate": 0.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees One Lakh Seventy-Four Thousand Six Hundred Forty Only",
    "terms": [
        "<b>Delivery:</b> 7 working days from date of formal Purchase Order issuance.",
        "<b>Warranty:</b> 2 Years standard manufacturer limited warranty including advance hardware replacement.",
        "<b>Payment Terms:</b> Net 30 days after delivery, installation check, and Goods Receipt Note (GRN) generation.",
        "<b>Tax Compliance:</b> E-Way bill and GST compliant tax invoice will accompany physical shipment.",
        "<b>Jurisdiction:</b> All legal matters governed under Jaipur (Rajasthan) judicial jurisdiction."
    ]
}

# 1.3 Jaipur IT Hardware & Systems
q3_it_jaipurit = {
    "primary_color": "#9A3412", # Terracotta / Deep Rust
    "secondary_color": "#FFEDD5",
    "company": {
        "name": "Jaipur IT Hardware & Systems",
        "tagline": "Authorized Institutional Systems Integrator & Hardware Stockist",
        "cin": "Reg No: RJ/JPR/COMM/88421",
        "gstin": "08AAAFJ5612P1ZN",
        "pan": "AAAFJ5612P",
        "udyam": "UDYAM-RJ-14-0012789",
        "address": "Shop 18-20, Ganpati Plaza, M.I. Road, Jaipur, Rajasthan - 302001",
        "email": "sales@jaipuritsystems.com",
        "phone": "+91 141 238 4501 / +91 98290 88771",
        "web": "www.jaipuritsystems.com",
        "bank": {
            "holder": "Jaipur IT Hardware & Systems",
            "name": "State Bank of India",
            "account": "38921104856",
            "ifsc": "SBIN0004128",
            "branch": "Commercial Branch, M.I. Road, Jaipur"
        },
        "signatory_title": "Proprietor / Chief Commercial Officer"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Information Technology",
        "contact_person": "Senior Manager - IT Procurement & Campus Computing"
    },
    "meta": {
        "quote_no": "JIT-2026-Q884",
        "quote_date": "14-Nov-2026",
        "validity": "15 Days",
        "valid_till": "29-Nov-2026",
        "rfq_ref": "AITM/IT/WEB-CAM/2026/044",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "Supply and On-Site Commissioning of 20 Poly Studio P5 Professional Webcams",
    "items": [
        {
            "name": "Poly Studio P5 Professional Full HD Business Webcam",
            "specs": "1080p FHD resolution, 80° diagonal field of view, 4x digital zoom, Exceptional optics tuned for professional video calls with automatic low-light compensation, Integrated directional microphone optimized for personal workspaces, Built-in mechanical privacy shutter, Removable monitor clamp.",
            "hsn": "85258900",
            "qty": 20,
            "unit": "Units",
            "rate": 8200.00
        },
        {
            "name": "On-Site Installation, Firmware Update & Audio-Video Calibration",
            "specs": "Deployment across 20 identified desktop and conference terminals, USB port driver integration, firmware upgrade to latest Poly Lens version, and live test report sign-off.",
            "hsn": "998713",
            "qty": 1,
            "unit": "Lot",
            "rate": 3500.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees One Lakh Ninety-Seven Thousand Six Hundred Fifty Only",
    "terms": [
        "<b>Delivery & Setup:</b> Ready ex-stock; deployment within 48 hours of Purchase Order receipt.",
        "<b>Warranty:</b> 2 Years comprehensive hardware warranty + 1 Year complimentary on-site engineer visit support.",
        "<b>Payment Terms:</b> 50% mobilization advance along with PO; remaining 50% post successful installation and sign-off.",
        "<b>Support SLA:</b> 4-hour response time for any malfunctioning unit in Jaipur municipal limits.",
        "<b>Jurisdiction:</b> Disputes subject strictly to Jaipur courts."
    ]
}


# -------------------------------------------------------------
# 2. IET DEPARTMENT (50 RASPBERRY PIs FOR STUDENTS)
# -------------------------------------------------------------

# 2.1 RoboCraft Electronics LLP
q4_iet_robocraft = {
    "primary_color": "#831843", # Deep Raspberry / Maroon
    "secondary_color": "#FCE7F3",
    "company": {
        "name": "RoboCraft Electronics LLP",
        "tagline": "Authorized Raspberry Pi Reseller & Institutional Robotics Hub",
        "cin": "LLPIN: AAN-4491",
        "gstin": "07AALFR4512D1ZR",
        "pan": "AALFR4512D",
        "udyam": "UDYAM-DL-08-0056120",
        "address": "D-42, Okhla Industrial Area, Phase-I, New Delhi - 110020",
        "email": "contact@robocraftelectronics.com",
        "phone": "+91 11 4188 9200 / +91 99100 88211",
        "web": "www.robocraftelectronics.com",
        "bank": {
            "holder": "RoboCraft Electronics LLP",
            "name": "Axis Bank Ltd",
            "account": "918020045612891",
            "ifsc": "UTIB0001248",
            "branch": "Okhla Phase 1, New Delhi"
        },
        "signatory_title": "Head of Institutional Sales & Academic Alliances"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Electronics & Information Technology (IET) - IoT Lab",
        "contact_person": "Dean (Academics) & Head of Department, IET"
    },
    "meta": {
        "quote_no": "RC/EDU/2026-11/045",
        "quote_date": "08-Nov-2026",
        "validity": "30 Days",
        "valid_till": "08-Dec-2026",
        "rfq_ref": "AITM/IET/LAB-RP/2026/012",
        "place_of_supply": "Rajasthan (State Code: 08 - Interstate Sale)"
    },
    "subject": "Supply of 50 Raspberry Pi 5 (8GB RAM) Lab Kits with Official Active Coolers & Power Supplies",
    "items": [
        {
            "name": "Raspberry Pi 5 Single Board Computer (8GB RAM Model)",
            "specs": "Broadcom BCM2712 2.4GHz quad-core 64-bit Arm Cortex-A76 CPU, 8GB LPDDR4X-4267 SDRAM, VideoCore VII GPU supporting dual 4Kp60 HDMI displays, PCIe 2.0 interface for high-speed peripherals, Dual-band 802.11ac Wi-Fi, Bluetooth 5.0 / BLE, Gigabit Ethernet, Official UK manufactured board.",
            "hsn": "84715000",
            "qty": 50,
            "unit": "Units",
            "rate": 7650.00
        },
        {
            "name": "Official Raspberry Pi 5 Active Cooler",
            "specs": "Single-piece anodized aluminum heatsink combined with a temperature-controlled variable-speed blower fan, pre-applied thermal pads, snap-in pin attachment.",
            "hsn": "84733099",
            "qty": 50,
            "unit": "Units",
            "rate": 520.00
        },
        {
            "name": "Official Raspberry Pi 27W USB-C PD Power Supply",
            "specs": "5.1V / 5.0A, 9.0V / 3.0A, 12.0V / 2.25A, 15.0V / 1.8A Power Delivery profile, BIS certified Indian 2-pin socket connector, 1.2m 17AWG captive cable.",
            "hsn": "85044090",
            "qty": 50,
            "unit": "Units",
            "rate": 1180.00
        },
        {
            "name": "SanDisk Ultra 64GB MicroSDXC UHS-I Card (Pre-Flashed)",
            "specs": "Class 10, A1 App Performance rating, up to 140MB/s transfer speeds, preloaded and verified with official Raspberry Pi OS (64-bit Bookworm with desktop).",
            "hsn": "85235100",
            "qty": 50,
            "unit": "Units",
            "rate": 480.00
        }
    ],
    "tax": {
        "is_igst": True,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees Five Lakh Seventy-Nine Thousand Nine Hundred Seventy Only",
    "terms": [
        "<b>Delivery:</b> Dispatched from New Delhi within 7-10 working days via insured blue-dart air cargo.",
        "<b>Warranty:</b> 1 Year standard manufacturer warranty on Raspberry Pi boards and 27W power supplies.",
        "<b>Payment Terms:</b> Net 30 days following physical receipt, lab verification, and institutional invoice submission.",
        "<b>GST Structure:</b> Interstate supply subject to 18% IGST with complete input tax credit (ITC) pass-through.",
        "<b>Jurisdiction:</b> Disputes subject to the jurisdiction of courts in New Delhi."
    ]
}

# 2.2 CircuitVerse Tech Hub Private Limited
q5_iet_circuitverse = {
    "primary_color": "#4338CA", # Indigo
    "secondary_color": "#E0E7FF",
    "company": {
        "name": "CircuitVerse Tech Hub Private Limited",
        "tagline": "Academic Lab Equipment, IoT Prototyping & Semiconductor Distribution",
        "cin": "U31909RJ2020PTC071239",
        "gstin": "08AAQFC3210M1ZU",
        "pan": "AAQFC3210M",
        "udyam": "UDYAM-RJ-14-0034981",
        "address": "C-14, Sitapura Industrial Area, Near RIICO Chowk, Jaipur, Rajasthan - 302022",
        "email": "lab-sales@circuitversetech.com",
        "phone": "+91 141 298 7100 / +91 97840 33445",
        "web": "www.circuitversetech.com",
        "bank": {
            "holder": "CircuitVerse Tech Hub Private Limited",
            "name": "Kotak Mahindra Bank",
            "account": "2814890012",
            "ifsc": "KKBK0003781",
            "branch": "Sitapura Industrial Area, Jaipur"
        },
        "signatory_title": "Director - Academic Systems & Solutions"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Electronics & Information Technology (IET)",
        "contact_person": "Lab In-Charge & Procurement Officer, IET"
    },
    "meta": {
        "quote_no": "CVT/LAB/7821",
        "quote_date": "11-Nov-2026",
        "validity": "15 Days",
        "valid_till": "26-Nov-2026",
        "rfq_ref": "AITM/IET/LAB-RP/2026/012",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "Supply of 50 Units of Raspberry Pi 5 (8GB) Custom Lab Bundles",
    "items": [
        {
            "name": "Raspberry Pi 5 Development Board (8GB LPDDR4X)",
            "specs": "2.4GHz quad-core 64-bit Arm Cortex-A76 CPU, 8GB high-speed memory, dual micro-HDMI 4K display ports, dual-lane MIPI camera/display transceivers, RTC battery connector, on-board power button.",
            "hsn": "84715000",
            "qty": 50,
            "unit": "Units",
            "rate": 7850.00
        },
        {
            "name": "Transparent Layered Acrylic Enclosure & Dual 5V Cooling Fans",
            "specs": "Laser-cut 9-layer acrylic chassis with GPIO cutout access, brass standoffs, and twin low-noise 5V brushless cooling fans.",
            "hsn": "84733099",
            "qty": 50,
            "unit": "Units",
            "rate": 410.00
        },
        {
            "name": "Heavy-Duty 27W Type-C Power Adapter (BIS Certified)",
            "specs": "Universal input 100-240V AC, 5.1V/5A constant output, short-circuit and over-voltage protection.",
            "hsn": "85044090",
            "qty": 50,
            "unit": "Units",
            "rate": 950.00
        },
        {
            "name": "Kingston Canvas Select Plus 64GB MicroSD Card",
            "specs": "UHS-I Class 10 speed rating up to 100MB/s read, SD adapter included.",
            "hsn": "85235100",
            "qty": 50,
            "unit": "Units",
            "rate": 440.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees Five Lakh Sixty-Nine Thousand Three Hundred Fifty Only",
    "terms": [
        "<b>Delivery:</b> Local Jaipur warehouse stock; delivered within 5 to 7 days from PO.",
        "<b>Warranty:</b> 1 Year replacement warranty; defective components swapped within 48 hours locally in Jaipur.",
        "<b>Payment Terms:</b> 100% payment within 15 days upon successful verification by the IET lab committee.",
        "<b>Assembly:</b> Complimentary pre-assembly of cases and fans upon request before dispatch.",
        "<b>Jurisdiction:</b> Exclusive legal jurisdiction of Jaipur courts."
    ]
}

# 2.3 SiliconEdge Component Distributors India Pvt. Ltd.
q6_iet_siliconedge = {
    "primary_color": "#374151", # Charcoal / Slate Grey
    "secondary_color": "#E5E7EB",
    "company": {
        "name": "SiliconEdge Component Distributors India Pvt. Ltd.",
        "tagline": "Direct Importers & Authorized Wholesale Stockists of Microcontrollers",
        "cin": "U51909MH2017PTC298412",
        "gstin": "27AAMCS6541L1Z2",
        "pan": "AAMCS6541L",
        "udyam": "UDYAM-MH-19-0012890",
        "address": "Unit 802, Trade Tower, Bandra Kurla Complex (BKC), Mumbai, Maharashtra - 400051",
        "email": "orders@siliconedge.co.in",
        "phone": "+91 22 6120 4400 / +91 98200 45678",
        "web": "www.siliconedge.co.in",
        "bank": {
            "holder": "SiliconEdge Component Distributors India Pvt. Ltd.",
            "name": "Standard Chartered Bank",
            "account": "22005481923",
            "ifsc": "SCBL0036001",
            "branch": "BKC Branch, Mumbai"
        },
        "signatory_title": "Vice President - Institutional Hardware Procurement"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Electronics & Information Technology (IET)",
        "contact_person": "Central Purchase Committee (Attention: IET Department)"
    },
    "meta": {
        "quote_no": "SEC/BULK/2026/1109",
        "quote_date": "13-Nov-2026",
        "validity": "20 Days",
        "valid_till": "03-Dec-2026",
        "rfq_ref": "AITM/IET/LAB-RP/2026/012",
        "place_of_supply": "Rajasthan (State Code: 08 - Interstate Sale)"
    },
    "subject": "Institutional Bulk Quotation: 50x Raspberry Pi 4 Model B (8GB) Lab Bundles",
    "items": [
        {
            "name": "Raspberry Pi 4 Model B (8GB RAM) [High Stability Lab Workhorse]",
            "specs": "Broadcom BCM2711 quad-core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz, 8GB LPDDR4-3200 SDRAM, 2.4GHz/5.0GHz IEEE 802.11ac Wi-Fi, 2x micro-HDMI ports (up to 4kp60 supported), 2x USB 3.0 and 2x USB 2.0 ports.",
            "hsn": "84715000",
            "qty": 50,
            "unit": "Units",
            "rate": 6200.00
        },
        {
            "name": "Official Raspberry Pi 4 Snap-fit ABS Case + Aluminum Heatsinks",
            "specs": "Red/White official enclosure with removable top cover and side panels, accompanied by set of 3 peel-and-stick aluminum heatsinks.",
            "hsn": "84733099",
            "qty": 50,
            "unit": "Units",
            "rate": 450.00
        },
        {
            "name": "Official Raspberry Pi 15.3W USB-C Power Supply",
            "specs": "5.1V / 3.0A DC output, Indian 2-pin integrated plug, official Raspberry Pi logo branded.",
            "hsn": "85044090",
            "qty": 50,
            "unit": "Units",
            "rate": 780.00
        },
        {
            "name": "Samsung EVO Plus 64GB MicroSDXC Memory Card",
            "specs": "UHS-I U1, Full HD video recording supported, up to 130MB/s read transfer speed, 10-year memory manufacturer warranty.",
            "hsn": "85235100",
            "qty": 50,
            "unit": "Units",
            "rate": 510.00
        }
    ],
    "tax": {
        "is_igst": True,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees Four Lakh Sixty-Eight Thousand Four Hundred Sixty Only",
    "terms": [
        "<b>Delivery:</b> 5 working days from Mumbai warehouse via surface express logistics.",
        "<b>Warranty:</b> 1 Year official manufacturer hardware replacement warranty.",
        "<b>Payment Terms:</b> 30% advance with official purchase order; balance 70% against delivery challan copy before unloading.",
        "<b>Educational Discount:</b> Special institutional tier rate applied; non-transferable.",
        "<b>Jurisdiction:</b> Disputes governed by courts in Mumbai, Maharashtra."
    ]
}


# -------------------------------------------------------------
# 3. MARKETING DEPARTMENT (JAIPUR PREMIUM BILLBOARDS)
# -------------------------------------------------------------

# 3.1 PinkCity Outdoor Advertising Media Private Limited
q7_mkt_pinkcity = {
    "primary_color": "#BE123C", # Rose / Crimson Red (Pink City theme)
    "secondary_color": "#FFE4E6",
    "company": {
        "name": "PinkCity Outdoor Advertising Media Private Limited",
        "tagline": "Jaipur's Largest Prime Out-of-Home (OOH) & Highway Media Network",
        "cin": "U74300RJ2015PTC047812",
        "gstin": "08AAAFP8901L1ZT",
        "pan": "AAAFP8901L",
        "udyam": "UDYAM-RJ-14-0019482",
        "address": "Landmark Tower, 5th Floor, Opp. SMS Stadium, Tonk Road, Jaipur, Rajasthan - 302015",
        "email": "campaigns@pinkcityoutdoor.com",
        "phone": "+91 141 410 8800 / +91 98290 77112",
        "web": "www.pinkcityoutdoor.com",
        "bank": {
            "holder": "PinkCity Outdoor Advertising Media Private Limited",
            "name": "IndusInd Bank Ltd",
            "account": "201002348911",
            "ifsc": "INDB0000058",
            "branch": "C-Scheme Branch, Jaipur"
        },
        "signatory_title": "Managing Director & Head of Media Planning"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Corporate Marketing & Brand Communications",
        "contact_person": "Chief Marketing Officer / Head - Branding & Public Relations"
    },
    "meta": {
        "quote_no": "PCO/OOH/JPR-2026-44",
        "quote_date": "09-Nov-2026",
        "validity": "15 Days",
        "valid_till": "24-Nov-2026",
        "rfq_ref": "AITM/MKT/OOH-JPR/2026/03",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "Comprehensive 3-Month Prime OOH Billboard Campaign Across Arterial Corridors in Jaipur",
    "items": [
        {
            "name": "Mega Unipole: JLN Marg, Directly Facing World Trade Park (North Facade)",
            "specs": "Size: 40ft (Width) × 20ft (Height) = 800 sq.ft. Front-lit with 6x 400W commercial LED flood fixtures. Prime visibility to premium shoppers, youth, and airport commuter corridor. Estimated daily vehicular & pedestrian reach: ~1,25,000. Display Period: 3 Consecutive Months (01-Dec-2026 to 28-Feb-2027) @ ₹1,85,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 185000.00
        },
        {
            "name": "High-Impact Gantry Billboard: Tonk Road, Gopalpura Flyover Junction",
            "specs": "Size: 50ft (Width) × 25ft (Height) = 1,250 sq.ft. Facing major incoming traffic flow toward Sitapura Industrial & Institutional hub. Unobstructed clear line-of-sight from 350 meters. Daily reach: ~1,50,000. Display Period: 3 Months @ ₹1,60,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 160000.00
        },
        {
            "name": "Heritage Commercial Hoarding: M.I. Road, Adjacent to Panch Batti Circle",
            "specs": "Size: 30ft (Width) × 20ft (Height) = 600 sq.ft. Back-lit display structure situated at Jaipur's iconic central business district. High dwell time during evening peak hours. Daily reach: ~95,000. Display Period: 3 Months @ ₹1,40,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 140000.00
        },
        {
            "name": "Heavy-Duty UV-Resistant Star Flex Printing, Rigging & Crane Mounting",
            "specs": "One-time cost covering high-resolution solvent print on 340 GSM heavy outdoor star flex, eyeleting, crane equipment, certified climbing riggers, and municipal electrical hookup across all 3 sites.",
            "hsn": "998362",
            "qty": 1,
            "unit": "Job",
            "rate": 45000.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees Seventeen Lakh Seventy Thousand Only",
    "terms": [
        "<b>Display Illumination:</b> Guaranteed daily illumination from 6:30 PM to 11:30 PM (5 hours daily).",
        "<b>Proof of Performance:</b> Weekly geo-tagged, timestamped high-resolution photographs (day & night) submitted via email.",
        "<b>Municipal Taxes:</b> All Jaipur Nagar Nigam (JNN) hoardings taxes, municipal ground rent, and electrical charges included.",
        "<b>Payment Terms:</b> 50% mobilization advance upon PO and artwork approval; balance 50% at exact midpoint of campaign (45 days).",
        "<b>Maintenance SLA:</b> In the event of wind/weather damage to flex, vendor guarantees replacement mounting within 36 hours at no extra charge.",
        "<b>Jurisdiction:</b> Exclusively courts at Jaipur, Rajasthan."
    ]
}

# 3.2 Rajputana Unipole & Hoardings LLP
q8_mkt_rajputana = {
    "primary_color": "#C2410C", # Burnt Orange / Amber
    "secondary_color": "#FFEDD5",
    "company": {
        "name": "Rajputana Unipole & Hoardings LLP",
        "tagline": "Highway Gantries, Elevated Corridors & City Entrance Outdoor Displays",
        "cin": "LLPIN: AAH-7120",
        "gstin": "08AAGFR2391Q1Z6",
        "pan": "AAGFR2391Q",
        "udyam": "UDYAM-RJ-14-0045231",
        "address": "12, Queens Road, Near Vaishali Nagar Circle, Jaipur, Rajasthan - 302021",
        "email": "rajputanamedia@yahoo.co.in",
        "phone": "+91 141 235 6900 / +91 94140 88290",
        "web": "www.rajputanamedia.in",
        "bank": {
            "holder": "Rajputana Unipole & Hoardings LLP",
            "name": "Punjab National Bank",
            "account": "0842002100049210",
            "ifsc": "PUNB0084200",
            "branch": "Vaishali Nagar, Jaipur"
        },
        "signatory_title": "Designated Managing Partner"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Marketing & Media Relations",
        "contact_person": "Senior Manager - Advertising & Media Buying"
    },
    "meta": {
        "quote_no": "RUHN/ADV/26-118",
        "quote_date": "11-Nov-2026",
        "validity": "10 Days",
        "valid_till": "21-Nov-2026",
        "rfq_ref": "AITM/MKT/OOH-JPR/2026/03",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "3-Month High-Visibility OOH Advertising Proposal for Arterial Jaipur Junctions",
    "items": [
        {
            "name": "Elevated Flyover Unipole: Ajmer Road, Sodala Approach Flyover",
            "specs": "Size: 35ft (W) × 20ft (H) = 700 sq.ft. Cantilever structure visible to both Delhi-Ajmer bypass traffic and commuters ascending elevated road. Daily traffic volume: ~1,10,000. Duration: 3 Months @ ₹1,35,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 135000.00
        },
        {
            "name": "Prime Rotational Unipole: JLN Marg, Near Jawahar Circle Rotary",
            "specs": "Size: 40ft (W) × 20ft (H) = 800 sq.ft. Front-lit with LED spots, situated at south entry point of JLN Marg connecting International Airport. Daily reach: ~1,00,000. Duration: 3 Months @ ₹1,70,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 170000.00
        },
        {
            "name": "Arterial Intersection Billboard: B2 Bypass Crossing & Mansarovar Entry",
            "specs": "Size: 45ft (W) × 20ft (H) = 900 sq.ft. Ground-mounted large format billboard targeting educational & residential clusters of Mansarovar. Daily reach: ~85,000. Duration: 3 Months @ ₹1,20,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 120000.00
        },
        {
            "name": "Fabrication, Blackout Star Flex Printing & Truss Clamping Work",
            "specs": "High quality 320 GSM Blackout flex printing to prevent rear light bleed, iron truss clamping, mounting labor across 3 locations.",
            "hsn": "998362",
            "qty": 1,
            "unit": "Job",
            "rate": 38000.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees Fifteen Lakh Forty-Nine Thousand Three Hundred Forty Only",
    "terms": [
        "<b>Illumination:</b> Standard 6:00 PM to 11:00 PM with automated timer switches.",
        "<b>Licensing:</b> All statutory Nagar Nigam Jaipur permits, safety clearances, and electricity charges are borne by vendor.",
        "<b>Payment Terms:</b> Monthly billing; payments to be cleared in advance on or before the 1st day of each operational month.",
        "<b>Artwork:</b> High-resolution print-ready CMYK open files (TIFF/CDR) to be supplied by client 5 days prior to mount date.",
        "<b>Jurisdiction:</b> Subject strictly to the courts of Jaipur."
    ]
}

# 3.3 Apex Jaipur Digital OOH & Media Solutions Pvt. Ltd.
q9_mkt_apexdooh = {
    "primary_color": "#15803D", # Emerald Green
    "secondary_color": "#DCFCE7",
    "company": {
        "name": "Apex Jaipur Digital OOH & Media Solutions Pvt. Ltd.",
        "tagline": "Next-Generation Smart Digital Screens (DOOH) & Iconic Media Assets",
        "cin": "U74999RJ2021PTC076541",
        "gstin": "08AAHCA7721N1ZY",
        "pan": "AAHCA7721N",
        "udyam": "UDYAM-RJ-14-0067812",
        "address": "4th Floor, City Pulse Complex, Narayan Singh Circle, Jaipur, Rajasthan - 302004",
        "email": "dooh@apexmediasolutions.in",
        "phone": "+91 141 491 2200 / +91 99280 44100",
        "web": "www.apexmediasolutions.in",
        "bank": {
            "holder": "Apex Jaipur Digital OOH & Media Solutions Pvt. Ltd.",
            "name": "Yes Bank Ltd",
            "account": "004583900001248",
            "ifsc": "YESB0000045",
            "branch": "Ashok Marg, C-Scheme, Jaipur"
        },
        "signatory_title": "Director - Digital Media & Strategic Accounts"
    },
    "client": {
        **CLIENT_AITM,
        "dept_name": "Department of Corporate Marketing & Brand Strategy",
        "contact_person": "Vice President - Corporate Affairs & Marketing Committee"
    },
    "meta": {
        "quote_no": "APX/DOOH/2026/092",
        "quote_date": "13-Nov-2026",
        "validity": "14 Days",
        "valid_till": "27-Nov-2026",
        "rfq_ref": "AITM/MKT/OOH-JPR/2026/03",
        "place_of_supply": "Rajasthan (State Code: 08)"
    },
    "subject": "Hybrid DOOH (Digital LED Screens) + Static Billboard 3-Month Campaign",
    "items": [
        {
            "name": "DOOH Premium Outdoor Screen: World Trade Park (WTP) North Atrium",
            "specs": "Ultra-bright 6500 nits P6 outdoor LED video wall (30ft × 18ft). Prime placement facing main commercial corridor. Slot: 10-second HD video/still creative running every 90 seconds (minimum 600 broadcast loops per day, 18 operating hours daily: 6 AM to 12 Midnight). 3 Months @ ₹1,50,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 150000.00
        },
        {
            "name": "DOOH Curved Digital Screen: Statue Circle / C-Scheme Rotary",
            "specs": "Curved high-resolution P4.8 LED screen (25ft × 15ft) positioned at premier high-net-worth bureaucratic and commercial roundabout. Slot: 10-second ad slot repeating every 90 seconds (600 plays daily). 3 Months @ ₹1,45,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 145000.00
        },
        {
            "name": "Static Front-Lit Billboard: Malviya Nagar Calgiri Hospital T-Point",
            "specs": "Size: 30ft (W) × 15ft (H) = 450 sq.ft. Front-lit static hoarding capturing traffic converging from JLN Marg toward Malviya Nagar market. Daily reach: ~70,000. 3 Months @ ₹95,000/month.",
            "hsn": "998361",
            "qty": 3,
            "unit": "Months",
            "rate": 95000.00
        },
        {
            "name": "Cloud CMS Ingestion, Telemetry Logging & 1 Static Flex Print/Mount",
            "specs": "Includes digital asset encoding, scheduling, live camera stream portal access, monthly computerized proof-of-play log, plus solvent flex printing and mounting for the static site.",
            "hsn": "998362",
            "qty": 1,
            "unit": "Job",
            "rate": 22000.00
        }
    ],
    "tax": {
        "is_igst": False,
        "rate_pct": 18.0
    },
    "total_in_words": "Rupees Fourteen Lakh Six Thousand Five Hundred Sixty Only",
    "terms": [
        "<b>Proof of Play:</b> Automated CMS software logs detailing exact broadcast timestamps, uptime percentage, and live webcam monitoring access provided to marketing team.",
        "<b>Creative Flexibility:</b> Client may update digital video creatives up to twice per calendar month at zero additional ingestion charge.",
        "<b>Payment Terms:</b> 100% advance for digital DOOH screen allocations on a monthly renewal cycle; static site billed net 15 days.",
        "<b>Electrical & Municipal:</b> Guaranteed 99% screen uptime backed by dedicated backup gensets and official Nagar Nigam licenses.",
        "<b>Jurisdiction:</b> Disputes governed exclusively by Jaipur judicial jurisdiction."
    ]
}

ALL_QUOTATIONS = [
    # IT Dept
    ("IT_01_TechNova_Peripherals_QT0891.pdf", q1_it_technova),
    ("IT_02_NexGen_Infotech_NOV442.pdf", q2_it_nexgen),
    ("IT_03_Jaipur_IT_Hardware_Q884.pdf", q3_it_jaipurit),
    # IET Dept
    ("IET_01_RoboCraft_Electronics_045.pdf", q4_iet_robocraft),
    ("IET_02_CircuitVerse_TechHub_7821.pdf", q5_iet_circuitverse),
    ("IET_03_SiliconEdge_Distributors_1109.pdf", q6_iet_siliconedge),
    # Marketing Dept
    ("Marketing_01_PinkCity_Outdoor_JPR44.pdf", q7_mkt_pinkcity),
    ("Marketing_02_Rajputana_Hoardings_ADV118.pdf", q8_mkt_rajputana),
    ("Marketing_03_Apex_Jaipur_DOOH_092.pdf", q9_mkt_apexdooh),
]

def main():
    print("=" * 60)
    print("STARTING GENERATION OF 9 COMPREHENSIVE QUOTATION PDFS")
    print("=" * 60)
    
    generated_files = []
    for filename, qdata in ALL_QUOTATIONS:
        out_path = os.path.join(OUTPUT_DIR, filename)
        build_quotation_pdf(qdata, out_path)
        generated_files.append(out_path)

    print("=" * 60)
    print(f"SUCCESSFULLY GENERATED ALL {len(generated_files)} PDF QUOTATIONS IN:")
    print(OUTPUT_DIR)
    print("=" * 60)

if __name__ == "__main__":
    main()
