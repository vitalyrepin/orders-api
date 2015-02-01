# Order management interface
# Vitaly Repin

// Person: Name, Surname, Middle name and (optiona) Title (Mr., Mrs., Dr. etc)
struct Person {
	1: string Name,
	2: string Surname,
	3: string MiddleName = "",
	4: optional string Title
}

// Delivery address. Only ISO/IEC 8859-15 characters are allowed
struct Address {
	1: Person To,
	2: string City,
	3: optional string State = "",
	4: string AddressLine1,
	5: string AddressLine2 = ""
	6: i64 ZIP,
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
enum PrintOrderStatus {
        RECEIVED = 1
	PROCESSING = 2,
	PRINTED = 3,
	SHIPPED = 4
}

// Possible error codes for order-related errors
enum PrintOrderErrCode {
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
	2: DeliveryMode delivery_mode,
	// Packaging selection
	3: PackagingMode packaging_mode
}

// Details of the product to be ordered
// Products codes are published at our web site
struct ProductData {
	1: string product_code,
	// Number of the document copies to manufacture
	2: byte qty
	// URL to fetch the document to print from
	3: string url
}

// Miscellaneous order details to be stored with the order. Optional
struct OrderMiscDetails {
	// Internal document id used by Customer
	1: string doc_id
	// Any text remark about the order
	2: string comment
}

// Order processing errors
exception PrintOrderError {
	1: PrintOrderErrCode Code,
	2: string _message
}

// OrderStatus / Time pair
struct OrderTimePair {
	// Unix timestamp - number of seconds since UNIX epoch
	1: i64 tm,
	2: PrintOrderStatus status
}

// This exception is used for general run-time errors
exception GeneralError {
	1: string OrderId,
	2: string _message
}

// Access denied errors
exception AccessDenied {
	1: string _message
}

// This service is used to manage Print & Delivery orders
service PrintAndDelivery {
	void ping(),
	string getAuthToken(1:string username, 2:string pswd) throws(1:AccessDenied adn),
	/**
	 * Puts new Purchase Order to the system
	 *
	 * @param string auth_token  Authentication token returned by getAuthToken method
	 * @param ShipmentData Shipment data (address, delivery mode, packaging selection)
	 * @param list<ProductData> product_data Products to be manufactuired (typically this list contains 1 product)
	 * @param OrderMiscDetails Miscellaneous details about the order (can be stored with the order and returned by getOrderDetails method
	*/
	string newOrder(1:string auth_token, 2:ShipmentData shipment, 3:list<ProductData> product_data, 4:OrderMiscDetails misc) throws (1:PrintOrderError oerr, 2:GeneralError gerr, 3:AccessDenied aerr),
	list<OrderTimePair>  getOrderDetails(1:string authToken, 2:string OrderId) throws(1:PrintOrderError oerr, 2:GeneralError gerr, 3:AccessDenied aerr)
}
