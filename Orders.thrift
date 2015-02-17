# Order management interface
# Vitaly Repin

// Person: Name, Surname, Middle name and (optiona) Title (Mr., Mrs., Dr. etc)
struct Person {
	1: string name,
	2: string surname,
	3: string middleName = "",
	4: optional string title
}

// Delivery address. Only ISO/IEC 8859-15 characters are allowed
struct Address {
	1: Person to,
	2: string city,
	3: optional string state = "",
	4: string addressLine1,
	5: string addressLine2 = ""
	6: i64 zip,
	// Country code according to ISO 3166-1 alpha-2
	7: string cc
}

// Possible delivery modes
enum DeliveryMode {
	// Economy-class delivery
	ECONOMY = 1,
	// Courier delivery: UPS carrier service
	COURIER_UPS = 2
}

// Possible packaging modes
enum PackagingMode {
	// Envelope
	ENVELOPE = 1,
	// Box
	BOX = 2
}

// Possible status of the printing orders
enum OrderStatus {
        RECEIVED = 1
	PROCESSING = 2,
	MANUFACTURED = 3,
	SHIPPED = 4,
	COMPLETED = 5
}

// Possible error codes for order-related errors
enum OrderErrCode {
	// Operation on non-existing order is requested
	INVALID_ID = 1,
	// Delivery is requested to the destination which is currently not served
	INVALID_ADDRESS = 2,
	// Service can't download the file to print using the URL given
	INVALID_PRINT_URL = 3
}

// Shipment details for the order
struct ShipmentData {
	// Delivery address
	1: Address address,
	// Delivery class
	2: DeliveryMode deliveryMode,
	// Packaging selection
	3: PackagingMode packagingMode
}

// Details of the product to be ordered
// Products codes are published at our web site
struct ProductData {
	1: string productCode,
	// Number of the document copies to manufacture
	2: byte qty
	// URL to fetch the document to print from
	3: string url
}

// Miscellaneous order details to be stored with the order. Optional
struct OrderMiscDetails {
	// Internal document id used by Customer
	1: string docId
	// Any text remark about the order
	2: string comment
}

// Order processing errors
exception OrderError {
	1: OrderErrCode code,
	2: string _message
}

// OrderStatus / Time pair
struct OrderTimePair {
	// Unix timestamp - number of seconds since UNIX epoch
	1: i64 tm,
	2: OrderStatus status
}

// This exception is used for general run-time errors
exception GeneralError {
	1: string orderId,
	2: string _message
}

// Access denied errors
exception AccessDenied {
	1: string _message
}

// This service is used to manage orders
service OrderManager {
	void ping(),
	string getAuthToken(1:string username, 2:string pswd) throws(1:AccessDenied adn),
	/**
	 * Puts new Purchase Order to the system
	 *
	 * @param string authToken  Authentication token returned by getAuthToken method
	 * @param ShipmentData Shipment data (address, deliveryMode, packaging selection)
	 * @param list<ProductData> productData Products to be manufactuired (typically this list contains 1 product)
	 * @param OrderMiscDetails Miscellaneous details about the order (can be stored with the order and returned by getOrderDetails method
	*/
	string newOrder(1:string authToken, 2:ShipmentData shipment, 3:list<ProductData> productData, 4:OrderMiscDetails misc) throws (1:OrderError oerr, 2:GeneralError gerr, 3:AccessDenied aerr),
	list<OrderTimePair>  getOrderDetails(1:string authToken, 2:string OrderId) throws(1:OrderError oerr, 2:GeneralError gerr, 3:AccessDenied aerr)
}
