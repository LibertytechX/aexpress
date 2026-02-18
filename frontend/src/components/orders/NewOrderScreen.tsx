'use client';

import React, { useState, useEffect, useRef } from 'react';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import AddressAutocompleteInput from '@/components/common/AddressAutocompleteInput';
import DeliveryMapView from '@/components/common/DeliveryMapView';
import API, { User } from '@/lib/api';

interface NewOrderScreenProps {
  balance: number;
  currentUser: User | null;
  onPlaceOrder: (orderData: any) => Promise<void>;
}

export default function NewOrderScreen({ balance, currentUser, onPlaceOrder }: NewOrderScreenProps) {
  // ─── Mode: "quick" | "multi" | "bulk" ───
  const [mode, setMode] = useState("quick");

  // ─── Shared state ───
  const [vehicle, setVehicle] = useState("Bike");
  const [payMethod, setPayMethod] = useState("wallet");
  const [step, setStep] = useState(1); // 1=form, 2=review

  // ─── Vehicle pricing from backend ───
  const [vehiclePricing, setVehiclePricing] = useState<Record<string, { base_fare: number, rate_per_km: number, rate_per_minute: number }>>({
    Bike: { base_fare: 500, rate_per_km: 50, rate_per_minute: 10 },
    Car: { base_fare: 1000, rate_per_km: 100, rate_per_minute: 20 },
    Van: { base_fare: 2000, rate_per_km: 200, rate_per_minute: 40 }
  });

  // ─── Early price estimation (Step 1) ───
  const [earlyRouteDistance, setEarlyRouteDistance] = useState<number | null>(null);
  const [earlyRouteDuration, setEarlyRouteDuration] = useState<number | null>(null);
  const [calculatingRoute, setCalculatingRoute] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);

  // ─── Pickup (shared across modes) ───
  const [pickupAddress, setPickupAddress] = useState("");
  const [senderName, setSenderName] = useState(currentUser?.contact_name || "");
  const [senderPhone, setSenderPhone] = useState(currentUser?.phone || "");

  // ─── Quick Send state ───
  const [dropoffAddress, setDropoffAddress] = useState("");
  const [receiverName, setReceiverName] = useState("");
  const [receiverPhone, setReceiverPhone] = useState("");
  const [notes, setNotes] = useState("");

  // ─── Multi-Drop state ───
  const [drops, setDrops] = useState([
    { id: 1, address: "", name: "", phone: "", pkg: "Box", notes: "" },
  ]);
  const nextDropId = useRef(2);

  // ─── Bulk Import state ───
  const [bulkText, setBulkText] = useState("");
  const [bulkRows, setBulkRows] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanPreview, setScanPreview] = useState<string | null>(null);

  // ─── Route information state (for pricing) ───
  const [routeDistance, setRouteDistance] = useState<number | null>(null); // in kilometers
  const [routeDuration, setRouteDuration] = useState<number | null>(null); // in minutes

  // Load vehicle pricing
  useEffect(() => {
    const loadVehiclePricing = async () => {
      try {
        const response = await API.Orders.getVehicles();
        if (response.success && response.vehicles) {
          const pricing: typeof vehiclePricing = {};
          response.vehicles.forEach(v => {
            pricing[v.name] = {
              base_fare: parseFloat(v.base_fare as any),
              rate_per_km: parseFloat(v.rate_per_km as any),
              rate_per_minute: parseFloat(v.rate_per_minute as any)
            };
          });
          setVehiclePricing(pricing);
        }
      } catch (error) {
        console.error('Failed to load vehicle pricing:', error);
      }
    };
    loadVehiclePricing();
  }, []);

  // Calculate early route
  useEffect(() => {
    if (mode !== 'quick' || !pickupAddress || !dropoffAddress) {
      setCalculatingRoute(false);
      setEarlyRouteDistance(null);
      setEarlyRouteDuration(null);
      setRouteError(null);
      return;
    }

    setEarlyRouteDistance(null);
    setEarlyRouteDuration(null);
    setRouteError(null);
    setCalculatingRoute(true);

    const calculateEarlyRoute = async () => {
      try {
        if (typeof window === 'undefined' || !(window as any).google || !(window as any).google.maps) {
          setRouteError('Maps not loaded');
          setCalculatingRoute(false);
          return;
        }

        const directionsService = new (window as any).google.maps.DirectionsService();
        const request = {
          origin: pickupAddress,
          destination: dropoffAddress,
          travelMode: (window as any).google.maps.TravelMode.DRIVING,
          drivingOptions: {
            departureTime: new Date(),
            trafficModel: (window as any).google.maps.TrafficModel.BEST_GUESS
          }
        };

        directionsService.route(request, (result: any, status: any) => {
          if (status === (window as any).google.maps.DirectionsStatus.OK && result.routes[0]) {
            const route = result.routes[0];
            let totalDistance = 0;
            let totalDuration = 0;

            route.legs.forEach((leg: any) => {
              totalDistance += leg.distance.value;
              totalDuration += leg.duration_in_traffic?.value || leg.duration.value;
            });

            const distanceKm = (totalDistance / 1000).toFixed(1);
            const durationMin = Math.ceil(totalDuration / 60);

            setEarlyRouteDistance(parseFloat(distanceKm));
            setEarlyRouteDuration(durationMin);
            setCalculatingRoute(false);
          } else {
            setRouteError('Unable to calculate route');
            setCalculatingRoute(false);
          }
        });
      } catch (error) {
        console.error('Error calculating route:', error);
        setRouteError('Error calculating route');
        setCalculatingRoute(false);
      }
    };

    const timeoutId = setTimeout(calculateEarlyRoute, 1000);
    return () => clearTimeout(timeoutId);
  }, [mode, pickupAddress, dropoffAddress]);

  // Load default address
  useEffect(() => {
    const loadDefaultAddress = async () => {
      try {
        const response = await API.Auth.getAddresses();
        // The API response type needs to be handled, simplistic check here
        const addresses = (response as any).addresses || [];
        if (addresses.length > 0) {
          const defaultAddress = addresses.find((addr: any) => addr.is_default);
          if (defaultAddress && defaultAddress.address) {
            setPickupAddress(defaultAddress.address);
          }
        }
      } catch (error) {
        console.error('Failed to load default address:', error);
      }
    };
    if (currentUser) {
      loadDefaultAddress();
    }
  }, [currentUser]);

  // Reset route data when going back to step 1
  useEffect(() => {
    if (step === 1) {
      setRouteDistance(null);
      setRouteDuration(null);
    }
  }, [step]);


  const addDrop = () => setDrops([...drops, { id: nextDropId.current++, address: "", name: "", phone: "", pkg: "Box", notes: "" }]);
  const removeDrop = (id: number) => drops.length > 1 && setDrops(drops.filter(d => d.id !== id));
  const updateDrop = (id: number, field: string, value: string) => setDrops(drops.map(d => d.id === id ? { ...d, [field]: value } : d));

  const parseBulkText = (text: string) => {
    const lines = text.trim().split("\n").filter(l => l.trim());
    return lines.map((line, i) => {
      const parts = line.includes("|") ? line.split("|") : line.includes("\t") ? line.split("\t") : line.split(",");
      return {
        id: i + 1,
        address: (parts[0] || "").trim(),
        name: (parts[1] || "").trim(),
        phone: (parts[2] || "").trim(),
        pkg: "Box",
        valid: (parts[0] || "").trim().length > 5,
      };
    });
  };

  const handleParseBulk = () => setBulkRows(parseBulkText(bulkText));

  const handleSnap = () => {
    setScanning(true);
    setScanPreview("/mock-scan.jpg");
    setTimeout(() => {
      setScanning(false);
      const mockOCR = [
        { id: 1, address: "15 Awolowo Rd, Ikoyi", name: "Mrs. Adeyemi", phone: "08034567890", pkg: "Box", valid: true },
        { id: 2, address: "22 Bode Thomas St, Surulere", name: "Chinedu O.", phone: "09098765432", pkg: "Envelope", valid: true },
      ];
      setBulkRows(mockOCR);
      setBulkText(mockOCR.map(r => `${r.address} | ${r.name} | ${r.phone}`).join("\n"));
    }, 2000);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setScanPreview(url);
      setScanning(true);
      setTimeout(() => {
        setScanning(false);
        setBulkRows([{ id: 1, address: "Mock Address", name: "Mock Name", phone: "000", pkg: "Box", valid: true }]);
      }, 2000);
    } else {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const text = ev.target?.result as string;
        setBulkText(text);
        setBulkRows(parseBulkText(text));
      };
      reader.readAsText(file);
    }
  }

  const getActiveDropoffs = () => {
    if (mode === "quick") return dropoffAddress ? [{ address: dropoffAddress, name: receiverName, phone: receiverPhone }] : [];
    if (mode === "multi") return drops.filter(d => d.address.trim());
    if (mode === "bulk") return bulkRows.filter(r => r.valid !== false && r.address.trim());
    return [];
  };

  const calculateCost = () => {
    const pricing = vehiclePricing[vehicle];
    if (!pricing) return 0;

    // Use confirmed route in Step 2
    if (step === 2 && routeDistance && routeDuration) {
      const distanceCost = routeDistance * pricing.rate_per_km;
      const timeCost = routeDuration * pricing.rate_per_minute;
      const total = pricing.base_fare + distanceCost + timeCost;
      return Math.round(total);
    }
    // Use early estimate in Step 1 (Quick mode only)
    if (mode === 'quick' && earlyRouteDistance && earlyRouteDuration) {
      const distanceCost = earlyRouteDistance * pricing.rate_per_km;
      const timeCost = earlyRouteDuration * pricing.rate_per_minute;
      const total = pricing.base_fare + distanceCost + timeCost;
      return Math.round(total);
    }
    // Fallback base fare
    return pricing.base_fare;
  };

  // const unitCost = calculateCost();
  const totalDeliveries = getActiveDropoffs().length;
  // const totalCost = totalDeliveries * unitCost; // Simplified: each delivery costs unitCost? Original code likely calculated based on total distance of route.
  // Actually, original code likely used total distance of the *whole route* for multi-drop, provided by Map.
  // In `DeliveryMapView`, the `routeDistance` is the total route distance.
  // So `calculateCost` using `routeDistance` essentially gives the total cost for the whole trip (assuming single vehicle).
  // The original code had `const totalCost = totalDeliveries * unitCost`? 
  // Let's check original code. 
  // Original code: `const totalCost = calculateCost();` (if it's one trip).
  // But wait, `DeliveryMapView` returns total distance of the trip.
  // If `mode === 'quick'`, totalDeliveries = 1.
  // If `mode === 'multi'`, the route covers all drops. So `routeDistance` is total distance.
  // So `unitCost` IS `totalCost` for the trip.

  function pricing_fallback(val: number) { return val || 0; }

  const finalTotalCost = step === 2 && routeDistance ? calculateCost() : (mode === 'quick' && earlyRouteDistance ? calculateCost() : pricing_fallback(vehiclePricing[vehicle]?.base_fare * totalDeliveries));

  const handleConfirmAll = async () => {
    const dropoffs = getActiveDropoffs();
    const orderData: any = {
      mode,
      pickup: pickupAddress,
      senderName,
      senderPhone,
      vehicle,
      payMethod,
      notes,
      distance_km: routeDistance || earlyRouteDistance || 0,
      duration_minutes: routeDuration || earlyRouteDuration || 0,
      amount: finalTotalCost,
      // For multi/bulk, pass list of deliveries
      deliveries: dropoffs.map((d: any) => ({
        dropoff_address: d.address,
        receiver_name: d.name,
        receiver_phone: d.phone,
        package_type: d.pkg || 'Box',
        notes: d.notes || notes
      }))
    };

    // Specifically for Quick Send, flatten if needed by `onPlaceOrder` (which expects flat props for quick)
    if (mode === 'quick' && dropoffs.length > 0) {
      orderData.dropoff = dropoffs[0].address;
      orderData.receiverName = (dropoffs[0] as any).name;
      orderData.receiverPhone = (dropoffs[0] as any).phone;
    }

    await onPlaceOrder(orderData);
  };

  return (
    <div style={{ display: "flex", gap: 24, paddingBottom: 40, height: "calc(100vh - 140px)" }}>
      {/* LEFT PANEL */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 24, overflowY: "auto", paddingRight: 4 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: S.navy, margin: "0 0 8px" }}>New Delivery</h2>
          <p style={{ color: S.gray, fontSize: 14, margin: 0 }}>
            {step === 1 ? "Get a rider instantly or schedule for later" : "Review details and confirm price"}
          </p>
        </div>

        {step === 1 && (
          <div style={{ background: "#fff", padding: 24, borderRadius: 16, border: "1px solid #e2e8f0", display: "flex", flexDirection: "column", gap: 24 }}>

            {/* Mode Selection */}
            <div style={{ display: "flex", background: "#f1f5f9", padding: 4, borderRadius: 10 }}>
              {["quick", "multi", "bulk"].map(m => (
                <button key={m} onClick={() => { setMode(m); setDrops([{ id: 1, address: "", name: "", phone: "", pkg: "Box", notes: "" }]); setBulkRows([]); }}
                  style={{
                    flex: 1, padding: "8px", borderRadius: 8, border: "none", cursor: "pointer",
                    background: mode === m ? "#fff" : "transparent",
                    color: mode === m ? S.navy : S.gray, fontWeight: 600, fontSize: 13,
                    boxShadow: mode === m ? "0 2px 8px rgba(0,0,0,0.05)" : "none",
                    transition: "all 0.2s"
                  }}
                >
                  {m === "quick" ? "⚡ Quick Send" : m === "multi" ? "📍 Multi-Drop" : "📂 Bulk Import"}
                </button>
              ))}
            </div>

            {/* Pickup */}
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 8 }}>Pickup From</label>
              <AddressAutocompleteInput value={pickupAddress} onChange={setPickupAddress} placeholder="Enter pickup address" style={{ width: "100%", height: 48, padding: "0 16px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
                <input value={senderName} onChange={e => setSenderName(e.target.value)} placeholder="Sender Name" style={{ height: 44, padding: "0 14px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
                <input value={senderPhone} onChange={e => setSenderPhone(e.target.value)} placeholder="Sender Phone" style={{ height: 44, padding: "0 14px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
              </div>
            </div>

            {/* QUICK MODE */}
            {mode === "quick" && (
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 8 }}>Deliver To</label>
                <AddressAutocompleteInput value={dropoffAddress} onChange={setDropoffAddress} placeholder="Enter dropoff address" style={{ width: "100%", height: 48, padding: "0 16px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
                {routeError && <div style={{ color: S.red, fontSize: 12, marginTop: 4 }}>{routeError}</div>}
                {calculatingRoute && <div style={{ color: S.gold, fontSize: 12, marginTop: 4 }}>Computing route...</div>}

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
                  <input value={receiverName} onChange={e => setReceiverName(e.target.value)} placeholder="Receiver Name" style={{ height: 44, padding: "0 14px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
                  <input value={receiverPhone} onChange={e => setReceiverPhone(e.target.value)} placeholder="Receiver Phone" style={{ height: 44, padding: "0 14px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
                </div>
                <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Delivery instructions (optional)" style={{ width: "100%", height: 80, padding: 14, borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14, marginTop: 12, fontFamily: "inherit", resize: "none" }} />
              </div>
            )}

            {/* MULTI MODE and BULK MODE ... (kept similar) */}
            {mode === "multi" && (
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 8 }}>Drop-off Locations</label>
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  {drops.map((drop, i) => (
                    <div key={drop.id} style={{ border: "1px solid #e2e8f0", borderRadius: 10, padding: 16, position: "relative" }}>
                      <div style={{ position: "absolute", top: 16, left: 16, width: 24, height: 24, borderRadius: "50%", background: S.gold, color: S.navy, fontSize: 12, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>{i + 1}</div>
                      {drops.length > 1 && (
                        <button onClick={() => removeDrop(drop.id)} style={{ position: "absolute", top: 16, right: 16, background: "none", border: "none", color: S.red, cursor: "pointer", fontSize: 18 }}>×</button>
                      )}
                      <div style={{ marginLeft: 36 }}>
                        <AddressAutocompleteInput value={drop.address} onChange={(val) => updateDrop(drop.id, "address", val)} placeholder="Dropoff address" style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 14, marginBottom: 12 }} />
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                          <input value={drop.name} onChange={(e) => updateDrop(drop.id, "name", e.target.value)} placeholder="Receiver Name" style={{ height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }} />
                          <input value={drop.phone} onChange={(e) => updateDrop(drop.id, "phone", e.target.value)} placeholder="Receiver Phone" style={{ height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }} />
                        </div>
                      </div>
                    </div>
                  ))}
                  <button onClick={addDrop} style={{ width: "100%", padding: "12px", border: "1px dashed #cbd5e1", borderRadius: 10, background: "#f8fafc", color: S.navy, fontWeight: 600, fontSize: 13, cursor: "pointer" }}>+ Add Another Dropoff</button>
                </div>
              </div>
            )}

            {mode === "bulk" && (
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 8 }}>Bulk Import</label>
                <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
                  <div style={{ flex: 1, position: "relative" }}>
                    <input type="file" accept="image/*,.csv,.txt" onChange={handleFileUpload} style={{ opacity: 0, position: "absolute", inset: 0, cursor: "pointer" }} />
                    <button style={{ width: "100%", height: 44, border: "1px solid #cbd5e1", borderRadius: 8, background: "#fff", color: S.navy, fontWeight: 600 }}>📂 Upload Photo/CSV</button>
                  </div>
                  <button onClick={handleSnap} style={{ flex: 1, height: 44, border: "1px solid #cbd5e1", borderRadius: 8, background: "#fff", color: S.navy, fontWeight: 600 }}>📷 Snap Photo</button>
                </div>

                {scanning ? (
                  <div style={{ height: 150, background: "#000", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff" }}>
                    Scannning...
                  </div>
                ) : (
                  <textarea value={bulkText} onChange={e => setBulkText(e.target.value)} placeholder={`Paste addresses or type here...\nFormat: Address | Name | Phone`} style={{ width: "100%", height: 120, padding: 14, borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 13, fontFamily: "inherit" }} />
                )}
                <button onClick={handleParseBulk} style={{ marginTop: 8, padding: "8px 16px", borderRadius: 8, background: S.navy, color: "#fff", border: "none", fontWeight: 600, fontSize: 13 }}>Parse Text</button>

                {bulkRows.length > 0 && (
                  <div style={{ marginTop: 16, border: "1px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
                    {bulkRows.map((row, i) => (
                      <div key={i} style={{ padding: 12, borderBottom: "1px solid #e2e8f0", fontSize: 13, display: "flex", justifyContent: "space-between", background: row.valid ? '#fff' : '#fee2e2' }}>
                        <span>{i + 1}. {row.address}</span>
                        <span>{row.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Vehicle Selection */}
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 12 }}>Select Vehicle</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                {Object.keys(vehiclePricing).map(vName => (
                  <button key={vName} onClick={() => setVehicle(vName)} style={{
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: 16,
                    borderRadius: 12, border: vehicle === vName ? `2px solid ${S.gold}` : "1px solid #e2e8f0",
                    background: vehicle === vName ? S.goldPale : "#fff", cursor: "pointer", transition: "all 0.2s"
                  }}>
                    <div style={{ color: vehicle === vName ? S.navy : S.gray }}>
                      {vName === 'Bike' ? Icons.bike : vName === 'Car' ? Icons.car : Icons.van}
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{vName}</span>
                    {mode === 'quick' && earlyRouteDistance && (
                      <span style={{ fontSize: 11, color: S.grayLight }}>
                        ₦{
                          Math.round((vehiclePricing[vName]?.base_fare || 0) + (earlyRouteDistance * (vehiclePricing[vName]?.rate_per_km || 0)) + (earlyRouteDuration || 0 * (vehiclePricing[vName]?.rate_per_minute || 0))).toLocaleString()
                        }
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Next Button */}
            <div style={{ paddingTop: 12 }}>
              <button onClick={() => setStep(2)} disabled={!pickupAddress || getActiveDropoffs().length === 0}
                style={{
                  width: "100%", padding: "16px", borderRadius: 12, border: "none",
                  background: (!pickupAddress || getActiveDropoffs().length === 0) ? '#e2e8f0' : S.navy,
                  color: (!pickupAddress || getActiveDropoffs().length === 0) ? '#94a3b8' : '#fff',
                  fontWeight: 700, fontSize: 15, cursor: (!pickupAddress || getActiveDropoffs().length === 0) ? "not-allowed" : "pointer"
                }}
              >
                Review & Get Price
              </button>
            </div>

          </div>
        )}

        {step === 2 && (
          <div style={{ background: "#fff", padding: 24, borderRadius: 16, border: "1px solid #e2e8f0", display: "flex", flexDirection: "column", gap: 24 }}>

            {/* Order Summary List */}
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: S.navy, borderBottom: `1px solid ${S.grayBg}`, paddingBottom: 12, marginBottom: 12 }}>Order Summary</h3>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 16 }}>
                <div style={{ marginTop: 2, color: S.green }}>{Icons.pin}</div>
                <div>
                  <div style={{ fontSize: 11, color: S.gray, fontWeight: 600 }}>PICKUP</div>
                  <div style={{ fontSize: 14, color: S.navy, fontWeight: 500 }}>{pickupAddress}</div>
                  <div style={{ fontSize: 12, color: S.gray }}>{senderName}, {senderPhone}</div>
                </div>
              </div>

              {getActiveDropoffs().map((d: any, i) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
                  <div style={{ marginTop: 2, color: S.gold }}>{Icons.pin}</div>
                  <div>
                    <div style={{ fontSize: 11, color: S.gray, fontWeight: 600 }}>DELIVERY #{i + 1}</div>
                    <div style={{ fontSize: 14, color: S.navy, fontWeight: 500 }}>{d.address}</div>
                    <div style={{ fontSize: 12, color: S.gray }}>{d.name}, {d.phone}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Payment Method */}
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: S.navy, marginBottom: 12 }}>Payment Method</h3>
              <div style={{ display: "flex", gap: 12 }}>
                <button onClick={() => setPayMethod('wallet')} style={{ flex: 1, padding: 12, border: payMethod === 'wallet' ? `2px solid ${S.navy}` : '1px solid #e2e8f0', borderRadius: 10, background: payMethod === 'wallet' ? '#f8fafc' : '#fff', textAlign: "left", cursor: "pointer" }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: S.navy, display: "flex", alignItems: "center", gap: 8 }}>
                    {Icons.wallet} Wallet
                  </div>
                  <div style={{ fontSize: 12, color: S.gray, marginTop: 4 }}>Balance: ₦{balance.toLocaleString()}</div>
                </button>
                <button onClick={() => setPayMethod('cash')} style={{ flex: 1, padding: 12, border: payMethod === 'cash' ? `2px solid ${S.navy}` : '1px solid #e2e8f0', borderRadius: 10, background: payMethod === 'cash' ? '#f8fafc' : '#fff', textAlign: "left", cursor: "pointer" }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: S.navy, display: "flex", alignItems: "center", gap: 8 }}>
                    ❄️ Cash
                  </div>
                  <div style={{ fontSize: 12, color: S.gray, marginTop: 4 }}>Pay on pickup/delivery</div>
                </button>
              </div>
            </div>

            {/* Total */}
            <div style={{ background: S.navy, padding: 20, borderRadius: 12, color: "#fff" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <span style={{ opacity: 0.8, fontSize: 13 }}>Total Cost</span>
                <span style={{ fontSize: 20, fontWeight: 700 }}>₦{finalTotalCost.toLocaleString()}</span>
              </div>
              {routeDistance && (
                <div style={{ fontSize: 12, opacity: 0.6 }}>Est. Distance: {routeDistance} km • Time: {routeDuration} mins</div>
              )}
            </div>

            {/* Buttons */}
            <div style={{ display: "flex", gap: 12 }}>
              <button onClick={() => setStep(1)} style={{ flex: 1, padding: 16, borderRadius: 12, border: "1px solid #e2e8f0", background: "#fff", color: S.navy, fontWeight: 700, cursor: "pointer" }}>Back</button>
              <button
                onClick={handleConfirmAll}
                disabled={payMethod === 'wallet' && finalTotalCost > balance}
                style={{
                  flex: 2, padding: 16, borderRadius: 12, border: "none",
                  background: (payMethod === 'wallet' && finalTotalCost > balance) ? '#e2e8f0' : S.navy,
                  color: (payMethod === 'wallet' && finalTotalCost > balance) ? '#94a3b8' : '#fff',
                  fontWeight: 700, cursor: (payMethod === 'wallet' && finalTotalCost > balance) ? "not-allowed" : "pointer"
                }}
              >
                {(payMethod === 'wallet' && finalTotalCost > balance) ? 'Insufficient Funds' : 'Confirm Order'}
              </button>
            </div>

          </div>
        )}
      </div>

      {/* RIGHT PANEL - MAP */}
      <div style={{ flex: 1, background: "#e2e8f0", borderRadius: 20, overflow: "hidden", position: "relative" }}>
        <DeliveryMapView
          pickupAddress={pickupAddress}
          dropoffs={getActiveDropoffs().map((d: any) => ({ address: d.address }))}
          vehicle={vehicle}
          totalDeliveries={getActiveDropoffs().length}
          totalCost={finalTotalCost}
          onRouteCalculated={(dist: number, time: number) => {
            setRouteDistance(dist);
            setRouteDuration(time);
          }}
        />
      </div>
    </div>
  );
}
