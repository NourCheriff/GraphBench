MATCH (o:Order {id: $order})<-[r]-(e:Event)
RETURN o, r, e
ORDER BY e.timestamp ASC
