# Order management interface
# Vitaly Repin

// Person: Name, Surname, Middle name and (optiona) Title (Mr., Mrs., Dr. etc)
struct Person {
	1: string Name,
	2: string Surname,
	3: string MiddleName = "",
	4: optional string Title
}

// Delivery address
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

// Possible status of the printing orders
enum PrintOrderStatus {
	PROCESSING = 1,
	PRINTED = 2,
	SHIPPED = 3
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
	string newOrder(1:string authToken, 2:Address Destination, 3:string URL, 4:string comment="") throws (1:PrintOrderError oerr, 2:GeneralError gerr, 3:AccessDenied aerr),
	list<OrderTimePair>  getOrderDetails(1:string authToken, 2:string OrderId) throws(1:PrintOrderError oerr, 2:GeneralError gerr, 3:AccessDenied aerr)
}