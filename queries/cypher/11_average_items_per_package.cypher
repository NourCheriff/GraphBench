MATCH (package:Package)-[:CONTAINS]->(item:Item)
RETURN
  round(toFloat(count(item)) / count(DISTINCT package), 2) AS averageItemsPerPackage
