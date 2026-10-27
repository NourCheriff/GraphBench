MATCH (product:Product)<-[:IS_A]-(item:Item)
RETURN product, count(item) AS itemsSold
ORDER BY itemsSold DESC
LIMIT 10
