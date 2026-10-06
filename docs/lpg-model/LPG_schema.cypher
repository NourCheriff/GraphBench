CREATE
    (:ProductPrice {
        value: "float",
        timestamp: "datetime"
    })
    <-[:HAS_PRICE]-
    (n5:Product {
        id: "string",
        weight: "float"
    })
    <-[:IS_A]-
    (n1:Item {
        id: "string",
        weight: "float",
        price: "float"
    })
    <-[:INVOLVES {
        qualifier: "string"
    }]-
    (n8:Event {
        id: "string",
        timestamp: "datetime"
    })
    -[:INVOLVES {
        qualifier: "string"
    }]->
    (n2:Package {
        id: "string",
        weight: "float"
    })
    -[:CONTAINS]->
    (n1),

    (n5)
    <-[:INVOLVES {
        qualifier: "string"
    }]-
    (n8)
    -[:INVOLVES {
        qualifier: "string"
    }]->
    (n3:Customer {
        id: "string"
    })
    -[:PLACES]->
    (n0:Order {
        id: "string",
        price: "float"
    })
    -[:INCLUDES]->
    (n1),

    (n2)
    -[:SHIPPED_BY]->
    (n4:Employee {
        id: "string",
        role: "string"
    })
    <-[:FORWARDED_BY]-
    (n2)
    -[:PACKED_BY]->
    (n4)
    <-[:INVOLVES {
        qualifier: "string"
    }]-
    (n8)
    -[:INVOLVES {
        qualifier: "string"
    }]->
    (n0),

    (n8)
    -[:OF_TYPE]->
    (:EventType {
        type: "string"
    }),

    (n4)
    -[:PRIMARY_SALES_REP]->
    (n3)
    <-[:SECONDARY_SALES_REP]-
    (n4);
