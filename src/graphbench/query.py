from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class QueryName(StrEnum):
    Q01_ORDER_EVENT_SEQUENCE = "01_order_event_sequence"          
    Q02_EVENT_OBJECTS = "02_event_objects"                        
    Q03_CUSTOMER_ORDERS = "03_customer_orders"                    
    Q04_ORDER_LEAD_TIME = "04_order_lead_time"                    
    Q05_AVERAGE_ORDER_LEAD_TIME = "05_average_order_lead_time"    
    Q06_PRODUCT_PRICE_HISTORY = "06_product_price_history"        
    Q07_TOP_SALES_REP = "07_top_sales_rep"                        
    Q08_TOP_CUSTOMER = "08_top_customer"                          
    Q09_TOP_SELLING_PRODUCTS = "09_top_selling_products"          
    Q10_FAILED_DELIVERY_RATIO = "10_failed_delivery_ratio"        
    Q11_AVERAGE_ITEMS_PER_PACKAGE = "11_average_items_per_package"
    Q12_SPLIT_ORDERS_RATIO = "12_split_orders_ratio"              
    Q13_TOP_SHIPPERS = "13_top_shippers"                          


@dataclass(frozen=True)
class Query:
    name: QueryName
    text: str  