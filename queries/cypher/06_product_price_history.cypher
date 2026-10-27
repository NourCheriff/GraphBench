MATCH (product:Product {id: "iPad Air"})-[:HAS_PRICE]->(price:ProductPrice)
RETURN product, price
ORDER BY price.timestamp DESC
