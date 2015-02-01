use orders

/// WARNING!  We clear users, products and subscriptions collections here. For development purposes. Don't use it on a live installation!
db.users.remove({})
db.products.remove({})
db.subscriptions.remove({})

db.users.insert({name: 'test', pswd: 'pswd', subscriptions: []})

/// Populating products collection
db.products.insert({name: 'MOOSEHEAD-VITT-100', description: '"Moose Head" watermark, white handmade paper'})
db.products.insert({name: 'MOOSETREE-GULT-100', description: '"Moose Tree" watermark, yellow tinted handmade paper'})
db.products.insert({name: 'IMPULSE-VITT-100', description: '"Impulse" watermark, white paper'})
db.products.insert({name: 'SHAMROCK-VITT-100', description: '"Shamrock" watermark, white paper'})
db.products.insert({name: 'LILY-VITT-120', description: '"Lily" watermark, white paper'})
db.products.insert({name: 'LESSEBO-VITT-200', description: 'White handmade paper with tiny "Lessebo" watermark'})
db.products.insert({name: 'LESSEBO-GULT-200', description: 'Yellow tinted handmade paper with tiny "Lessebo" watermark'})

/// Populating subscriptions collection
db.subscriptions.insert({name: "S", description: '< 100'})
db.subscriptions.insert({name: "M", description: '100 - 1000'})
db.subscriptions.insert({name: "L", description: '1000 - 5000'})
db.subscriptions.insert({name: "XL", description: '5000 - 10000'})

