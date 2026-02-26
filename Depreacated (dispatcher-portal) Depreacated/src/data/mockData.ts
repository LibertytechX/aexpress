import type { Rider, Order, Merchant, Customer, Chat } from "../types";

export const INIT_RIDERS: Rider[] = [
    { id: "R001", name: "Musa Kabiru", phone: "08034561234", vehicle: "Bike", status: "online", currentOrder: "AX-6158260", todayOrders: 8, todayEarnings: 14400, rating: 4.8, totalDeliveries: 1234, completionRate: 96, avgTime: "28 min", joined: "Sep 2024" },
    { id: "R002", name: "Ahmed Bello", phone: "09012349876", vehicle: "Bike", status: "online", currentOrder: "AX-6158258", todayOrders: 6, todayEarnings: 10800, rating: 4.6, totalDeliveries: 876, completionRate: 94, avgTime: "32 min", joined: "Nov 2024" },
    { id: "R003", name: "Chinedu Okoro", phone: "07055667788", vehicle: "Car", status: "on_delivery", currentOrder: "AX-6158261", todayOrders: 4, todayEarnings: 18000, rating: 4.9, totalDeliveries: 567, completionRate: 98, avgTime: "35 min", joined: "Jan 2025" },
    { id: "R004", name: "Tunde Adewale", phone: "08199887766", vehicle: "Van", status: "offline", currentOrder: null, todayOrders: 0, todayEarnings: 0, rating: 4.5, totalDeliveries: 345, completionRate: 92, avgTime: "42 min", joined: "Oct 2024" },
    { id: "R005", name: "Ibrahim Suleiman", phone: "08088776655", vehicle: "Bike", status: "online", currentOrder: null, todayOrders: 5, todayEarnings: 9000, rating: 4.7, totalDeliveries: 2100, completionRate: 97, avgTime: "25 min", joined: "Jun 2024" },
    { id: "R006", name: "Kola Adekunle", phone: "07033445566", vehicle: "Car", status: "on_delivery", currentOrder: "AX-6158263", todayOrders: 3, todayEarnings: 13500, rating: 4.4, totalDeliveries: 198, completionRate: 91, avgTime: "38 min", joined: "Dec 2024" },
    { id: "R007", name: "Emeka Nwankwo", phone: "09044332211", vehicle: "Bike", status: "online", currentOrder: null, todayOrders: 7, todayEarnings: 12600, rating: 4.8, totalDeliveries: 1567, completionRate: 95, avgTime: "26 min", joined: "Aug 2024" },
    { id: "R008", name: "Femi Akinola", phone: "08155443322", vehicle: "Bike", status: "offline", currentOrder: null, todayOrders: 9, todayEarnings: 16200, rating: 4.9, totalDeliveries: 3200, completionRate: 99, avgTime: "22 min", joined: "Mar 2024" },
];

export const INIT_ORDERS: Order[] = [
    { id: "AX-6158260", customer: "Adebayo Johnson", customerPhone: "08034567890", merchant: "Vivid Print", pickup: "24 Harvey Rd, Sabo Yaba", dropoff: "15 Akin Adesola St, VI", rider: "Musa Kabiru", riderId: "R001", status: "In Transit", amount: 1210, cod: 55000, codFee: 500, vehicle: "Bike", created: "Feb 14, 3:42 PM", pkg: "Box" },
    { id: "AX-6158261", customer: "Chidi Obi", customerPhone: "07011223344", merchant: "Mama Nkechi Kitchen", pickup: "8 Bode Thomas, Surulere", dropoff: "22 Ozumba Mbadiwe, VI", rider: "Chinedu Okoro", riderId: "R003", status: "Picked Up", amount: 4500, cod: 0, codFee: 0, vehicle: "Car", created: "Feb 14, 3:28 PM", pkg: "Food" },
    { id: "AX-6158262", customer: "Funke Adeyemi", customerPhone: "09012345678", merchant: "TechZone Gadgets", pickup: "Computer Village, Ikeja", dropoff: "45 Admiralty Way, Lekki", rider: null, riderId: null, status: "Pending", amount: 4500, cod: 210000, codFee: 500, vehicle: "Car", created: "Feb 14, 3:15 PM", pkg: "Fragile" },
    { id: "AX-6158263", customer: "Emeka Eze", customerPhone: "09044332211", merchant: "AutoParts Hub", pickup: "12 Agege Motor Rd, Mushin", dropoff: "33 Allen Avenue, Ikeja", rider: "Kola Adekunle", riderId: "R006", status: "In Transit", amount: 4500, cod: 45000, codFee: 500, vehicle: "Car", created: "Feb 14, 2:55 PM", pkg: "Box" },
    { id: "AX-6158258", customer: "Blessing Nwosu", customerPhone: "08155667788", merchant: "GlowUp Beauty", pickup: "10 Adeola Odeku, VI", dropoff: "7 Admiralty Rd, Lekki Phase 1", rider: "Ahmed Bello", riderId: "R002", status: "Assigned", amount: 1210, cod: 0, codFee: 0, vehicle: "Bike", created: "Feb 14, 2:40 PM", pkg: "Envelope" },
    { id: "AX-6158257", customer: "Ngozi Ibe", customerPhone: "07088990011", merchant: "Vivid Print", pickup: "24 Harvey Rd, Sabo Yaba", dropoff: "5 Karimu Kotun, VI", rider: "Musa Kabiru", riderId: "R001", status: "Delivered", amount: 1210, cod: 36000, codFee: 500, vehicle: "Bike", created: "Feb 14, 1:20 PM", pkg: "Box" },
    { id: "AX-6158256", customer: "Kola Peters", customerPhone: "08144556677", merchant: "TechZone Gadgets", pickup: "Computer Village, Ikeja", dropoff: "14 Toyin St, Ikeja", rider: "Ibrahim Suleiman", riderId: "R005", status: "Delivered", amount: 1210, cod: 125000, codFee: 500, vehicle: "Bike", created: "Feb 14, 12:50 PM", pkg: "Fragile" },
    { id: "AX-6158255", customer: "Aisha Mohammed", customerPhone: "07055443322", merchant: "FreshFit Lagos", pickup: "3 Admiralty Way, Lekki", dropoff: "20 Fola Osibo, Lekki Phase 1", rider: "Emeka Nwankwo", riderId: "R007", status: "Delivered", amount: 1210, cod: 0, codFee: 0, vehicle: "Bike", created: "Feb 14, 11:30 AM", pkg: "Envelope" },
    { id: "AX-6158254", customer: "Adebayo Johnson", customerPhone: "08034567890", merchant: "Vivid Print", pickup: "24 Harvey Rd, Sabo Yaba", dropoff: "15 Akin Adesola St, VI", rider: null, riderId: null, status: "Cancelled", amount: 1210, cod: 0, codFee: 0, vehicle: "Bike", created: "Feb 14, 10:15 AM", pkg: "Document" },
    { id: "AX-6158253", customer: "Chidi Obi", customerPhone: "07011223344", merchant: "Mama Nkechi Kitchen", pickup: "8 Bode Thomas, Surulere", dropoff: "1 Glover Rd, Ikoyi", rider: "Ahmed Bello", riderId: "R002", status: "Delivered", amount: 4500, cod: 75000, codFee: 500, vehicle: "Car", created: "Feb 13, 5:40 PM", pkg: "Food" },
    { id: "AX-6158252", customer: "Emeka Eze", customerPhone: "09044332211", merchant: "AutoParts Hub", pickup: "12 Agege Motor Rd, Mushin", dropoff: "8 Opebi Rd, Ikeja", rider: "Kola Adekunle", riderId: "R006", status: "Failed", amount: 4500, cod: 18000, codFee: 500, vehicle: "Car", created: "Feb 13, 4:10 PM", pkg: "Box" },
    { id: "AX-6158251", customer: "Funke Adeyemi", customerPhone: "09012345678", merchant: "GlowUp Beauty", pickup: "10 Adeola Odeku, VI", dropoff: "25 Adetokunbo Ademola, VI", rider: "Femi Akinola", riderId: "R008", status: "Delivered", amount: 1210, cod: 8500, codFee: 500, vehicle: "Bike", created: "Feb 13, 3:00 PM", pkg: "Box" },
];

export const MERCHANTS_DATA: Merchant[] = [
    { id: "M001", name: "Vivid Print", contact: "Ogun Lami", phone: "08051832508", category: "Printing", totalOrders: 234, monthOrders: 42, walletBalance: 87900, status: "Active", joined: "Nov 2024" },
    { id: "M002", name: "TechZone Gadgets", contact: "Ade Bakare", phone: "09012345678", category: "Electronics", totalOrders: 567, monthOrders: 89, walletBalance: 234500, status: "Active", joined: "Sep 2024" },
    { id: "M003", name: "Mama Nkechi Kitchen", contact: "Nkechi Obi", phone: "07033445566", category: "Food", totalOrders: 1203, monthOrders: 156, walletBalance: 56700, status: "Active", joined: "Jul 2024" },
    { id: "M004", name: "FreshFit Lagos", contact: "Sola Adams", phone: "08055667788", category: "Fashion", totalOrders: 89, monthOrders: 12, walletBalance: 12300, status: "Active", joined: "Jan 2025" },
    { id: "M005", name: "GlowUp Beauty", contact: "Amara Eze", phone: "08022334455", category: "Beauty", totalOrders: 445, monthOrders: 67, walletBalance: 178000, status: "Active", joined: "Aug 2024" },
    { id: "M006", name: "AutoParts Hub", contact: "Bayo Ogun", phone: "08099887766", category: "Auto Parts", totalOrders: 312, monthOrders: 34, walletBalance: 45600, status: "Inactive", joined: "Oct 2024" },
];

export const CUSTOMERS_DATA: Customer[] = [
    { id: "C001", name: "Adebayo Johnson", phone: "08034567890", email: "adebayo@gmail.com", totalOrders: 15, lastOrder: "Feb 14", totalSpent: 182500, favMerchant: "Vivid Print" },
    { id: "C002", name: "Funke Adeyemi", phone: "09012345678", email: "funke.a@yahoo.com", totalOrders: 8, lastOrder: "Feb 13", totalSpent: 94000, favMerchant: "TechZone Gadgets" },
    { id: "C003", name: "Chidi Obi", phone: "07011223344", email: "chidi.obi@outlook.com", totalOrders: 23, lastOrder: "Feb 14", totalSpent: 567000, favMerchant: "Mama Nkechi" },
    { id: "C004", name: "Blessing Nwosu", phone: "08155667788", email: "blessing.n@gmail.com", totalOrders: 5, lastOrder: "Feb 12", totalSpent: 42000, favMerchant: "GlowUp Beauty" },
    { id: "C005", name: "Emeka Eze", phone: "09044332211", email: "emeka.eze@gmail.com", totalOrders: 31, lastOrder: "Feb 14", totalSpent: 890000, favMerchant: "AutoParts Hub" },
    { id: "C006", name: "Ngozi Ibe", phone: "07088990011", email: "ngozi.ibe@yahoo.com", totalOrders: 12, lastOrder: "Feb 13", totalSpent: 156000, favMerchant: "Vivid Print" },
    { id: "C007", name: "Kola Peters", phone: "08144556677", email: "kpeters@gmail.com", totalOrders: 19, lastOrder: "Feb 14", totalSpent: 345000, favMerchant: "TechZone Gadgets" },
    { id: "C008", name: "Aisha Mohammed", phone: "07055443322", email: "aisha.m@outlook.com", totalOrders: 7, lastOrder: "Feb 11", totalSpent: 78500, favMerchant: "FreshFit Lagos" },
];

export const MSG_RIDER: Chat[] = [
    { id: "R001", name: "Musa Kabiru", unread: 2, lastMsg: "On my way to pickup now", lastTime: "4:05 PM", messages: [{ from: "dispatch", text: "Musa, new order AX-6158260 assigned. Pickup at Sabo Yaba.", time: "3:44 PM" }, { from: "rider", text: "Received. Heading there now.", time: "3:45 PM" }, { from: "rider", text: "Traffic heavy on Third Mainland. ETA 12 mins.", time: "3:50 PM" }, { from: "dispatch", text: "Noted. Customer informed.", time: "3:51 PM" }, { from: "rider", text: "On my way to pickup now", time: "4:05 PM" }] },
    { id: "R003", name: "Chinedu Okoro", unread: 0, lastMsg: "Package secured, heading out", lastTime: "3:35 PM", messages: [{ from: "dispatch", text: "Chinedu, AX-6158261 for you. Car required — food delivery.", time: "3:28 PM" }, { from: "rider", text: "Copy. 5 mins from Surulere pickup.", time: "3:30 PM" }, { from: "rider", text: "Package secured, heading out", time: "3:35 PM" }] },
    { id: "R005", name: "Ibrahim Suleiman", unread: 1, lastMsg: "Free for next dispatch", lastTime: "1:15 PM", messages: [{ from: "rider", text: "AX-6158256 delivered. COD collected.", time: "1:10 PM" }, { from: "dispatch", text: "Great work! Settle COD via wallet.", time: "1:12 PM" }, { from: "rider", text: "Done. Free for next dispatch", time: "1:15 PM" }] },
];

export const MSG_CUSTOMER: Chat[] = [
    { id: "C001", name: "Adebayo Johnson", unread: 1, lastMsg: "When will my package arrive?", lastTime: "4:08 PM", messages: [{ from: "customer", text: "Hi, I placed AX-6158260. Any update?", time: "4:02 PM" }, { from: "dispatch", text: "Your rider Musa is en route. ETA ~15 min.", time: "4:04 PM" }, { from: "customer", text: "When will my package arrive?", time: "4:08 PM" }] },
    { id: "C003", name: "Chidi Obi", unread: 0, lastMsg: "Thank you!", lastTime: "3:40 PM", messages: [{ from: "customer", text: "Is my food order on the way?", time: "3:30 PM" }, { from: "dispatch", text: "Yes! Chinedu picked it up. Heading to you now.", time: "3:36 PM" }, { from: "customer", text: "Thank you!", time: "3:40 PM" }] },
];
