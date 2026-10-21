/** Major airports for search suggestions. Any valid 3-letter IATA code can also be typed directly. */
export interface Airport { code: string; city: string; name: string; country: string }

const row = (code: string, city: string, name: string, country: string): Airport => ({code, city, name, country});

export const AIRPORTS: Airport[] = [
  // India
  row("DEL", "Delhi", "Indira Gandhi International", "India"),
  row("BOM", "Mumbai", "Chhatrapati Shivaji Maharaj International", "India"),
  row("NMI", "Navi Mumbai", "Navi Mumbai International", "India"),
  row("BLR", "Bengaluru", "Kempegowda International", "India"),
  row("MAA", "Chennai", "Chennai International", "India"),
  row("CCU", "Kolkata", "Netaji Subhas Chandra Bose International", "India"),
  row("HYD", "Hyderabad", "Rajiv Gandhi International", "India"),
  row("GOI", "Goa", "Dabolim", "India"),
  row("GOX", "Goa", "Manohar International (Mopa)", "India"),
  row("COK", "Kochi", "Cochin International", "India"),
  row("TRV", "Thiruvananthapuram", "Trivandrum International", "India"),
  row("AMD", "Ahmedabad", "Sardar Vallabhbhai Patel International", "India"),
  row("PNQ", "Pune", "Pune", "India"),
  row("JAI", "Jaipur", "Jaipur International", "India"),
  row("LKO", "Lucknow", "Chaudhary Charan Singh International", "India"),
  row("ATQ", "Amritsar", "Sri Guru Ram Dass Jee International", "India"),
  row("IXC", "Chandigarh", "Chandigarh International", "India"),
  row("SXR", "Srinagar", "Srinagar", "India"),
  row("IXJ", "Jammu", "Jammu", "India"),
  row("IXL", "Leh", "Kushok Bakula Rimpochee", "India"),
  row("VNS", "Varanasi", "Lal Bahadur Shastri International", "India"),
  row("PAT", "Patna", "Jay Prakash Narayan", "India"),
  row("GAY", "Gaya", "Gaya", "India"),
  row("GAU", "Guwahati", "Lokpriya Gopinath Bordoloi International", "India"),
  row("BBI", "Bhubaneswar", "Biju Patnaik International", "India"),
  row("IXB", "Bagdogra", "Bagdogra (for Darjeeling, Sikkim)", "India"),
  row("CCJ", "Kozhikode", "Calicut International", "India"),
  row("IXE", "Mangaluru", "Mangaluru International", "India"),
  row("CJB", "Coimbatore", "Coimbatore International", "India"),
  row("IXM", "Madurai", "Madurai", "India"),
  row("TRZ", "Tiruchirappalli", "Tiruchirappalli International", "India"),
  row("IXZ", "Port Blair", "Veer Savarkar International", "India"),
  row("UDR", "Udaipur", "Maharana Pratap", "India"),
  row("JDH", "Jodhpur", "Jodhpur", "India"),
  row("IDR", "Indore", "Devi Ahilya Bai Holkar", "India"),
  row("BHO", "Bhopal", "Raja Bhoj", "India"),
  row("NAG", "Nagpur", "Dr. Babasaheb Ambedkar International", "India"),
  row("RPR", "Raipur", "Swami Vivekananda", "India"),
  row("VTZ", "Visakhapatnam", "Visakhapatnam", "India"),
  row("VGA", "Vijayawada", "Vijayawada", "India"),
  row("TIR", "Tirupati", "Tirupati", "India"),
  row("IXR", "Ranchi", "Birsa Munda", "India"),
  row("DED", "Dehradun", "Jolly Grant", "India"),
  row("DHM", "Dharamshala", "Kangra (Gaggal)", "India"),
  row("KUU", "Kullu", "Bhuntar (for Manali)", "India"),
  row("IXA", "Agartala", "Maharaja Bir Bikram", "India"),
  row("IMF", "Imphal", "Bir Tikendrajit International", "India"),
  row("STV", "Surat", "Surat", "India"),
  row("BDQ", "Vadodara", "Vadodara", "India"),
  row("HBX", "Hubballi", "Hubballi", "India"),
  // Nearby and Asia-Pacific
  row("CMB", "Colombo", "Bandaranaike International", "Sri Lanka"),
  row("MLE", "Malé", "Velana International", "Maldives"),
  row("KTM", "Kathmandu", "Tribhuvan International", "Nepal"),
  row("DAC", "Dhaka", "Hazrat Shahjalal International", "Bangladesh"),
  row("PBH", "Paro", "Paro International", "Bhutan"),
  row("SIN", "Singapore", "Changi", "Singapore"),
  row("KUL", "Kuala Lumpur", "Kuala Lumpur International", "Malaysia"),
  row("BKK", "Bangkok", "Suvarnabhumi", "Thailand"),
  row("DMK", "Bangkok", "Don Mueang", "Thailand"),
  row("HKT", "Phuket", "Phuket International", "Thailand"),
  row("CGK", "Jakarta", "Soekarno–Hatta International", "Indonesia"),
  row("DPS", "Bali", "Ngurah Rai International (Denpasar)", "Indonesia"),
  row("MNL", "Manila", "Ninoy Aquino International", "Philippines"),
  row("SGN", "Ho Chi Minh City", "Tan Son Nhat International", "Vietnam"),
  row("HAN", "Hanoi", "Noi Bai International", "Vietnam"),
  row("HKG", "Hong Kong", "Hong Kong International", "Hong Kong"),
  row("TPE", "Taipei", "Taoyuan International", "Taiwan"),
  row("ICN", "Seoul", "Incheon International", "South Korea"),
  row("NRT", "Tokyo", "Narita International", "Japan"),
  row("HND", "Tokyo", "Haneda", "Japan"),
  row("KIX", "Osaka", "Kansai International", "Japan"),
  row("PEK", "Beijing", "Capital International", "China"),
  row("PKX", "Beijing", "Daxing International", "China"),
  row("PVG", "Shanghai", "Pudong International", "China"),
  row("CAN", "Guangzhou", "Baiyun International", "China"),
  row("SYD", "Sydney", "Kingsford Smith", "Australia"),
  row("MEL", "Melbourne", "Melbourne (Tullamarine)", "Australia"),
  row("BNE", "Brisbane", "Brisbane", "Australia"),
  row("PER", "Perth", "Perth", "Australia"),
  row("AKL", "Auckland", "Auckland", "New Zealand"),
  // Middle East and Africa
  row("DXB", "Dubai", "Dubai International", "United Arab Emirates"),
  row("AUH", "Abu Dhabi", "Zayed International", "United Arab Emirates"),
  row("SHJ", "Sharjah", "Sharjah International", "United Arab Emirates"),
  row("DOH", "Doha", "Hamad International", "Qatar"),
  row("MCT", "Muscat", "Muscat International", "Oman"),
  row("BAH", "Bahrain", "Bahrain International", "Bahrain"),
  row("KWI", "Kuwait City", "Kuwait International", "Kuwait"),
  row("RUH", "Riyadh", "King Khalid International", "Saudi Arabia"),
  row("JED", "Jeddah", "King Abdulaziz International", "Saudi Arabia"),
  row("IST", "Istanbul", "Istanbul", "Türkiye"),
  row("CAI", "Cairo", "Cairo International", "Egypt"),
  row("NBO", "Nairobi", "Jomo Kenyatta International", "Kenya"),
  row("ADD", "Addis Ababa", "Bole International", "Ethiopia"),
  row("JNB", "Johannesburg", "O. R. Tambo International", "South Africa"),
  row("CPT", "Cape Town", "Cape Town International", "South Africa"),
  // Europe
  row("LHR", "London", "Heathrow", "United Kingdom"),
  row("LGW", "London", "Gatwick", "United Kingdom"),
  row("MAN", "Manchester", "Manchester", "United Kingdom"),
  row("DUB", "Dublin", "Dublin", "Ireland"),
  row("CDG", "Paris", "Charles de Gaulle", "France"),
  row("ORY", "Paris", "Orly", "France"),
  row("AMS", "Amsterdam", "Schiphol", "Netherlands"),
  row("BRU", "Brussels", "Brussels", "Belgium"),
  row("FRA", "Frankfurt", "Frankfurt", "Germany"),
  row("MUC", "Munich", "Munich", "Germany"),
  row("ZRH", "Zurich", "Zurich", "Switzerland"),
  row("GVA", "Geneva", "Geneva", "Switzerland"),
  row("VIE", "Vienna", "Vienna International", "Austria"),
  row("PRG", "Prague", "Václav Havel", "Czechia"),
  row("FCO", "Rome", "Fiumicino", "Italy"),
  row("MXP", "Milan", "Malpensa", "Italy"),
  row("MAD", "Madrid", "Adolfo Suárez Madrid–Barajas", "Spain"),
  row("BCN", "Barcelona", "Josep Tarradellas Barcelona–El Prat", "Spain"),
  row("LIS", "Lisbon", "Humberto Delgado", "Portugal"),
  row("ATH", "Athens", "Athens International", "Greece"),
  row("CPH", "Copenhagen", "Copenhagen", "Denmark"),
  row("ARN", "Stockholm", "Arlanda", "Sweden"),
  row("OSL", "Oslo", "Gardermoen", "Norway"),
  row("HEL", "Helsinki", "Helsinki-Vantaa", "Finland"),
  // Americas
  row("JFK", "New York", "John F. Kennedy International", "United States"),
  row("EWR", "New York", "Newark Liberty International", "United States"),
  row("BOS", "Boston", "Logan International", "United States"),
  row("IAD", "Washington", "Dulles International", "United States"),
  row("ORD", "Chicago", "O'Hare International", "United States"),
  row("ATL", "Atlanta", "Hartsfield–Jackson International", "United States"),
  row("DFW", "Dallas", "Dallas Fort Worth International", "United States"),
  row("IAH", "Houston", "George Bush Intercontinental", "United States"),
  row("MIA", "Miami", "Miami International", "United States"),
  row("LAX", "Los Angeles", "Los Angeles International", "United States"),
  row("SFO", "San Francisco", "San Francisco International", "United States"),
  row("SEA", "Seattle", "Seattle–Tacoma International", "United States"),
  row("YYZ", "Toronto", "Pearson International", "Canada"),
  row("YVR", "Vancouver", "Vancouver International", "Canada"),
  row("YUL", "Montreal", "Trudeau International", "Canada"),
  row("MEX", "Mexico City", "Benito Juárez International", "Mexico"),
  row("GRU", "São Paulo", "Guarulhos International", "Brazil"),
  row("EZE", "Buenos Aires", "Ezeiza International", "Argentina"),
];

const BY_CODE = new Map(AIRPORTS.map(airport => [airport.code, airport]));

function fold(value: string) {
  return value.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
}

export function airportByCode(code: string) {
  return BY_CODE.get(code.trim().toUpperCase());
}

export function airportLabel(airport: Airport) {
  return `${airport.city} (${airport.code})`;
}

/** Best matches first: exact code, then city prefix, then city/name/country contains. */
export function searchAirports(query: string, limit = 8): Airport[] {
  const q = fold(query);
  if (!q) return [];
  const scored: [number, Airport][] = [];
  for (const airport of AIRPORTS) {
    const city = fold(airport.city), name = fold(airport.name), country = fold(airport.country);
    const score = airport.code.toLowerCase() === q ? 0 : city.startsWith(q) ? 1 : city.includes(q) ? 2
      : name.includes(q) ? 3 : country.startsWith(q) ? 4 : -1;
    if (score >= 0) scored.push([score, airport]);
  }
  return scored.sort((a, b) => a[0] - b[0]).slice(0, limit).map(([, airport]) => airport);
}

/** Resolve typed text: a known label like "Goa (GOI)", any 3-letter code, or a city with one clear airport. */
export function resolveAirport(text: string): string | null {
  const value = text.trim();
  const labelled = value.match(/\(([A-Za-z]{3})\)\s*$/);
  if (labelled) return labelled[1].toUpperCase();
  if (/^[A-Za-z]{3}$/.test(value)) return value.toUpperCase();
  const city = AIRPORTS.filter(airport => fold(airport.city) === fold(value));
  return city.length ? city[0].code : null;
}
