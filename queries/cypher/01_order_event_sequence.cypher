MATCH (o:Order {id: "o-990679"})<-[r]-(e:Event)
RETURN o, r, e
ORDER BY e.timestamp ASC
