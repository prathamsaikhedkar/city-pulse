export const gwaliorLocations = [
  { id: 1, name: "Gwalior Fort", lat: 26.2300, lng: 78.1691, description: "The historic heart and highest point of the city." },
  { id: 2, name: "Lashkar", lat: 26.2031, lng: 78.1610, description: "The traditional central business district and palace area." },
  { id: 3, name: "Gole Ka Mandir", lat: 26.2465, lng: 78.2045, description: "A major transit hub connecting to the northern outskirts." },
  { id: 4, name: "Hazira", lat: 26.2392, lng: 78.1795, description: "An industrial and densely populated residential zone." },
  { id: 5, name: "Morar", lat: 26.2238, lng: 78.2255, description: "Formerly a separate cantonment, now a bustling eastern wing." },
  { id: 6, name: "City Centre", lat: 26.2120, lng: 78.1944, description: "The modern administrative and upscale commercial hub." },
  { id: 7, name: "Thatipur", lat: 26.2163, lng: 78.2098, description: "A prominent residential government colony area." },
  { id: 8, name: "Phool Bagh", lat: 26.2195, lng: 78.1744, description: "A central cultural area housing parks, museums, and shrines." },
  { id: 9, name: "Dabra (Outskirts)", lat: 25.8900, lng: 78.3300, description: "The southern gateway and industrial satellite region." },
  { id: 10, name: "DD Nagar", lat: 26.2580, lng: 78.2180, description: "A planned residential township towards the northeast." },
  { id: 11, name: "Sada (New Gwalior)", lat: 26.1950, lng: 78.0800, description: "The counter-magnet city area being developed to the west." },
  { id: 12, name: "Kampoo", lat: 26.1965, lng: 78.1565, description: "A historic southern area known for hospitals and sports." },
  { id: 13, name: "Birla Nagar", lat: 26.2485, lng: 78.1885, description: "An industrial belt centered around the railway station." },
  { id: 14, name: "Tansen Nagar", lat: 26.2355, lng: 78.1905, description: "A residential area named after the legendary musician." },
  { id: 15, name: "Hurawali", lat: 26.2040, lng: 78.2320, description: "A fast-developing residential zone on the eastern edge." }
];

const getRandom = (min, max) => Math.random() * (max - min) + min;

export const generateMockAQIData = (locationId) => {
  const data = [];
  const now = new Date();
  
  let baseAqi = 80;
  if ([4, 13, 9].includes(locationId)) baseAqi += 40;
  if ([1, 11].includes(locationId)) baseAqi -= 20;

  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    
    const hour = time.getHours();
    const timeEffect = (hour > 8 && hour < 20) ? 20 : 0;
    
    const currentAqi = Math.max(10, Math.round(baseAqi + timeEffect + getRandom(-15, 15)));
    
    data.push({
      time: time.toISOString(),
      location_id: locationId,
      aqi: currentAqi,
      pm2_5: Math.max(1, currentAqi * getRandom(0.4, 0.6)),
      pm10: Math.max(1, currentAqi * getRandom(0.6, 0.9)),
      co: getRandom(0.1, 1.5),
      no2: getRandom(5, 30),
      o3: getRandom(10, 50),
      so2: getRandom(2, 10),
      temperature: getRandom(15, 35),
      humidity: getRandom(30, 80)
    });
  }
  return data;
};

export const useAllMockData = () => {
    const dataMap = {};
    gwaliorLocations.forEach(loc => {
        dataMap[loc.id] = generateMockAQIData(loc.id);
    });
    return dataMap;
};

