"""Real geography for the synthetic hospital corpus.

Hospitals are invented; the places they sit in are not. Using real localities
with real coordinates means distances, travel-time estimates and "hospitals
near me" behave the way a user from that city expects, and the demo is legible
to anyone who knows the city.

`cost_index` scales CGHS base package rates to local price levels. It is a
city-level multiplier; per-hospital positioning is layered on top of it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Locality:
    name: str
    lat: float
    lon: float
    affluence: float
    """0-1. Drives how upmarket the hospitals placed here tend to be, which
    shows up in room tariffs and accreditation odds."""


@dataclass(frozen=True)
class City:
    name: str
    state: str
    cost_index: float
    pincode_prefix: str
    phone_std: str
    localities: list[Locality] = field(default_factory=list)
    schemes: tuple[str, ...] = ()
    """State scheme slugs available here, matching GovernmentScheme values."""

    @property
    def slug(self) -> str:
        return self.name.lower().replace(" ", "_")


BENGALURU = City(
    name="Bengaluru",
    state="Karnataka",
    cost_index=1.00,
    pincode_prefix="560",
    phone_std="080",
    schemes=("pmjay", "cghs", "esi", "arogya_karnataka", "yeshaswini"),
    localities=[
        Locality("Indiranagar", 12.9784, 77.6408, 0.85),
        Locality("Koramangala", 12.9352, 77.6245, 0.88),
        Locality("Whitefield", 12.9698, 77.7500, 0.80),
        Locality("Jayanagar", 12.9250, 77.5938, 0.72),
        Locality("Malleshwaram", 13.0035, 77.5709, 0.70),
        Locality("Rajajinagar", 12.9915, 77.5520, 0.58),
        Locality("HSR Layout", 12.9116, 77.6389, 0.84),
        Locality("BTM Layout", 12.9166, 77.6101, 0.62),
        Locality("Electronic City", 12.8452, 77.6602, 0.68),
        Locality("Marathahalli", 12.9591, 77.6974, 0.66),
        Locality("Hebbal", 13.0358, 77.5970, 0.74),
        Locality("Yeshwanthpur", 13.0287, 77.5540, 0.55),
        Locality("Banashankari", 12.9250, 77.5667, 0.60),
        Locality("JP Nagar", 12.9077, 77.5851, 0.71),
        Locality("Basavanagudi", 12.9422, 77.5736, 0.66),
        Locality("Richmond Town", 12.9611, 77.6000, 0.82),
        Locality("Shivajinagar", 12.9857, 77.6055, 0.48),
        Locality("Vijayanagar", 12.9719, 77.5308, 0.54),
        Locality("Kengeri", 12.9081, 77.4850, 0.42),
        Locality("Bannerghatta Road", 12.8900, 77.5970, 0.76),
        Locality("Sarjapur Road", 12.9010, 77.6870, 0.79),
        Locality("Bellandur", 12.9260, 77.6762, 0.77),
        Locality("Yelahanka", 13.1007, 77.5963, 0.63),
        Locality("KR Puram", 13.0076, 77.6960, 0.50),
        Locality("Nagarbhavi", 12.9600, 77.5100, 0.47),
        Locality("Peenya", 13.0280, 77.5190, 0.40),
        Locality("Domlur", 12.9611, 77.6387, 0.80),
        Locality("Frazer Town", 12.9985, 77.6135, 0.64),
        Locality("Jalahalli", 13.0400, 77.5200, 0.44),
        Locality("Kammanahalli", 13.0150, 77.6400, 0.58),
    ],
)

DELHI = City(
    name="Delhi NCR",
    state="Delhi",
    cost_index=1.18,
    pincode_prefix="110",
    phone_std="011",
    schemes=("pmjay", "cghs", "esi", "delhi_aarogya_kosh"),
    localities=[
        Locality("Saket", 28.5245, 77.2066, 0.86),
        Locality("Dwarka", 28.5921, 77.0460, 0.68),
        Locality("Rohini", 28.7495, 77.0565, 0.60),
        Locality("Karol Bagh", 28.6519, 77.1909, 0.58),
        Locality("Vasant Kunj", 28.5200, 77.1591, 0.88),
        Locality("Lajpat Nagar", 28.5677, 77.2433, 0.70),
        Locality("Pitampura", 28.6942, 77.1314, 0.64),
        Locality("Janakpuri", 28.6219, 77.0878, 0.62),
        Locality("Mayur Vihar", 28.6089, 77.2954, 0.58),
        Locality("Shalimar Bagh", 28.7167, 77.1500, 0.61),
        Locality("Connaught Place", 28.6315, 77.2167, 0.84),
        Locality("Noida Sector 62", 28.6280, 77.3649, 0.72),
        Locality("Gurugram Sector 44", 28.4499, 77.0700, 0.90),
        Locality("Faridabad", 28.4089, 77.3178, 0.52),
        Locality("Ghaziabad", 28.6692, 77.4538, 0.50),
    ],
)

MUMBAI = City(
    name="Mumbai",
    state="Maharashtra",
    cost_index=1.26,
    pincode_prefix="400",
    phone_std="022",
    schemes=("pmjay", "cghs", "esi", "mjpjay"),
    localities=[
        Locality("Andheri West", 19.1364, 72.8296, 0.82),
        Locality("Bandra", 19.0596, 72.8295, 0.92),
        Locality("Dadar", 19.0178, 72.8478, 0.70),
        Locality("Powai", 19.1176, 72.9060, 0.85),
        Locality("Mulund", 19.1726, 72.9425, 0.66),
        Locality("Borivali", 19.2307, 72.8567, 0.64),
        Locality("Thane", 19.2183, 72.9781, 0.60),
        Locality("Vashi", 19.0770, 72.9986, 0.68),
        Locality("Parel", 19.0000, 72.8400, 0.76),
        Locality("Malad", 19.1860, 72.8484, 0.63),
        Locality("Chembur", 19.0522, 72.9005, 0.65),
        Locality("Goregaon", 19.1663, 72.8526, 0.67),
    ],
)

HYDERABAD = City(
    name="Hyderabad",
    state="Telangana",
    cost_index=0.94,
    pincode_prefix="500",
    phone_std="040",
    schemes=("pmjay", "cghs", "esi", "aarogyasri"),
    localities=[
        Locality("Banjara Hills", 17.4126, 78.4392, 0.90),
        Locality("Jubilee Hills", 17.4239, 78.4738, 0.91),
        Locality("Gachibowli", 17.4400, 78.3489, 0.83),
        Locality("Secunderabad", 17.4399, 78.4983, 0.64),
        Locality("Kukatpally", 17.4849, 78.4138, 0.58),
        Locality("Madhapur", 17.4485, 78.3908, 0.80),
        Locality("Begumpet", 17.4400, 78.4600, 0.72),
        Locality("LB Nagar", 17.3457, 78.5522, 0.48),
        Locality("Somajiguda", 17.4256, 78.4571, 0.74),
        Locality("Miyapur", 17.4960, 78.3600, 0.55),
    ],
)

CITIES: list[City] = [BENGALURU, DELHI, MUMBAI, HYDERABAD]

# Hospitals per city. Bengaluru is built out in depth so the demo has a city
# where every filter, tariff and network lookup has enough data behind it to
# behave realistically; the others prove the model is not city-specific.
HOSPITAL_COUNTS: dict[str, int] = {
    "Bengaluru": 250,
    "Delhi NCR": 120,
    "Mumbai": 120,
    "Hyderabad": 90,
}

CITY_BY_NAME: dict[str, City] = {c.name: c for c in CITIES}