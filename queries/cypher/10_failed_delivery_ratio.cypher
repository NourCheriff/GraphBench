MATCH (e:Event)
WHERE e.type IN ["failed delivery", "package delivered"]
RETURN toFloat(count(CASE WHEN e.type = "failed delivery" THEN 1 END)) / count(e) AS failureRate
