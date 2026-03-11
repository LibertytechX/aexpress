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
  // Defaults mirror the production tiered pricing so the UI is correct even
  // before the API response arrives (or if it fails).
  const [vehiclePricing, setVehiclePricing] = useState<Record<string, any>>({
    Bike: {
      base_fare: 0, rate_per_km: 275, rate_per_minute: 0,
      pricing_tiers: {
        type: 'tiered', floor_km: 6, floor_fee: 1700,
        tiers: [{ max_km: 10, rate: 275 }, { max_km: 15, rate: 235 }, { rate: 200 }]
      }
    },
    Car: {
      base_fare: 0, rate_per_km: 350, rate_per_minute: 0,
      pricing_tiers: {
        type: 'tiered', floor_km: 3, floor_fee: 2500,
        tiers: [{ max_km: 8, rate: 350 }, { max_km: 15, rate: 300 }, { rate: 250 }]
      }
    },
    Van: {
      base_fare: 0, rate_per_km: 500, rate_per_minute: 0,
      pricing_tiers: {
        type: 'tiered', floor_km: 3, floor_fee: 5000,
        tiers: [{ max_km: 8, rate: 500 }, { max_km: 15, rate: 450 }, { rate: 400 }]
      }
    },
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
  const [estimatedCost, setEstimatedCost] = useState(null);

  // ─── Same-address validation ───
  const [sameAddressError, setSameAddressError] = useState("");

  // Normalise addresses for comparison (lower, trim, collapse spaces)
  const normaliseAddr = (s: string) => s.toLowerCase().trim().replace(/\s+/g, " ");

  // Reactively detect same address — fires whenever either field changes,
  // regardless of HOW the value was set (typing, autocomplete selection, etc.)
  useEffect(() => {
    if (pickupAddress && dropoffAddress && normaliseAddr(pickupAddress) === normaliseAddr(dropoffAddress)) {
      setSameAddressError("same-quick");
    } else {
      setSameAddressError("");
    }
  }, [pickupAddress, dropoffAddress]);

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
          const pricing: any = {};
          response.vehicles.forEach((v: any) => {
            pricing[v.name] = {
              base_fare: parseFloat(v.base_fare),
              rate_per_km: parseFloat(v.rate_per_km),
              rate_per_minute: parseFloat(v.rate_per_minute),
              pricing_tiers: typeof v.pricing_tiers === 'string' ? JSON.parse(v.pricing_tiers) : (v.pricing_tiers || null),
            };
          });
          setVehiclePricing(pricing);
          console.log('✅ Loaded vehicle pricing from backend:', pricing);
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

  // ─── Tiered price calculation (rate-switch with boundary floors) ───
  const calcTieredPrice = (km: number, pt: any) => {
    if (!pt || pt.type !== 'tiered') return null;
    if (km <= pt.floor_km) return pt.floor_fee;
    const t = pt.tiers || [];
    if (t[0] && km <= t[0].max_km) return Math.max(Math.round(km * t[0].rate), pt.floor_fee);
    if (t[1] && km <= t[1].max_km) return Math.max(Math.round(km * t[1].rate), Math.round((t[0]?.max_km || pt.floor_km) * (t[0]?.rate || 0)));
    if (t[2]) return Math.max(Math.round(km * t[2].rate), Math.round((t[1]?.max_km || 0) * (t[1]?.rate || 0)));
    return Math.round(km * (t[t.length - 1]?.rate || 0));
  };

  // ─── Price calculation ───
  // Calculate price for a specific vehicle using early route data
  const calculateEarlyPrice = (vehicleName: string) => {
    if (!earlyRouteDistance || !earlyRouteDuration) return null;

    const pricing = vehiclePricing[vehicleName];
    if (!pricing) return null;

    // Use tiered pricing if available
    const tiered = calcTieredPrice(earlyRouteDistance, pricing.pricing_tiers);
    if (tiered !== null) return tiered;

    const distanceCost = earlyRouteDistance * pricing.rate_per_km;
    const timeCost = earlyRouteDuration * pricing.rate_per_minute;
    return Math.round(pricing.base_fare + distanceCost + timeCost);
  };

  const getActiveDropoffs = () => {
    if (mode === "quick") return dropoffAddress ? [{ address: dropoffAddress, name: receiverName, phone: receiverPhone }] : [];
    if (mode === "multi") return drops.filter(d => d.address.trim());
    if (mode === "bulk") return bulkRows.filter(r => r.valid !== false && r.address.trim());
    return [];
  };

  const totalDeliveries = getActiveDropoffs().length;

  // Calculate dynamic cost based on route distance and duration
  const calculateCost = () => {
    const pricing = vehiclePricing[vehicle];
    if (!pricing) return 0;

    // Step 2 uses the full route (map) calculation.
    if (step === 2 && routeDistance && routeDuration) {
      const tiered = calcTieredPrice(routeDistance, pricing.pricing_tiers);
      if (tiered !== null) return tiered;
      return Math.round(pricing.base_fare + routeDistance * pricing.rate_per_km + routeDuration * pricing.rate_per_minute);
    }

    // Step 1 (Quick Send): if we already calculated an early route, use it
    if (mode === 'quick' && earlyRouteDistance && earlyRouteDuration) {
      const tiered = calcTieredPrice(earlyRouteDistance, pricing.pricing_tiers);
      if (tiered !== null) return tiered;
      return Math.round(pricing.base_fare + earlyRouteDistance * pricing.rate_per_km + earlyRouteDuration * pricing.rate_per_minute);
    }

    // Fallback: floor fee for tiered, or base fare for simple
    if (pricing.pricing_tiers?.type === 'tiered') return pricing.pricing_tiers.floor_fee;
    return pricing.base_fare;
  };

  const unitCost = calculateCost();
  const totalCost = totalDeliveries * unitCost;

  // ─── Review & Confirm ───
  const isBlank = (v: any) => !v || !String(v).trim();
  const proceedErrors: string[] = [];

  if (isBlank(pickupAddress)) proceedErrors.push('Pickup address is required.');
  if (isBlank(senderName)) proceedErrors.push('Sender name is required.');
  if (isBlank(senderPhone)) proceedErrors.push('Sender phone is required.');

  if (mode === 'quick') {
    if (isBlank(dropoffAddress)) proceedErrors.push('Delivery address is required.');
    if (isBlank(receiverName)) proceedErrors.push('Receiver name is required.');
    if (isBlank(receiverPhone)) proceedErrors.push('Receiver phone is required.');
    if (pickupAddress && dropoffAddress && normaliseAddr(pickupAddress) === normaliseAddr(dropoffAddress)) {
      proceedErrors.push('Pickup and dropoff address cannot be the same.');
    }
  } else if (mode === 'multi' || mode === 'bulk') {
    if (totalDeliveries <= 0) proceedErrors.push('At least one delivery is required.');
    const active = getActiveDropoffs();
    const missingReceiver = active.some((d: any) => isBlank(d.name) || isBlank(d.phone));
    if (missingReceiver) proceedErrors.push('Receiver name and phone are required for all deliveries.');
    const hasSameAddr = active.some((d: any) => d.address && pickupAddress && normaliseAddr(pickupAddress) === normaliseAddr(d.address));
    if (hasSameAddr) proceedErrors.push('One or more dropoff addresses match the pickup address.');
  }

  const canProceed = proceedErrors.length === 0;
  const showProceedErrors = !canProceed && (
    totalDeliveries > 0 ||
    (mode === 'quick' && !isBlank(dropoffAddress)) ||
    (mode === 'multi' && drops.some(d => !isBlank(d.address) || !isBlank(d.name) || !isBlank(d.phone))) ||
    (mode === 'bulk' && (!isBlank(bulkText) || bulkRows.length > 0))
  );

  const [submitting, setSubmitting] = useState(false);

  const handleConfirmAll = async () => {
    if (submitting) return;
    const deliveries = getActiveDropoffs();

    // Prepare order data based on mode
    const orderData: any = {
      mode: mode,
      pickup: pickupAddress,
      senderName: senderName,
      senderPhone: senderPhone,
      vehicle: vehicle,
      payMethod: payMethod,
      notes: notes,
      // Include route information for pricing calculation.
      // Prefer the map-calculated distance (Step 2); fall back to the early
      // estimate (Step 1) so the backend never receives 0 when the user
      // submits before DeliveryMapView finishes its geocode/route request.
      distance_km: routeDistance || earlyRouteDistance || 0,
      duration_minutes: routeDuration || earlyRouteDuration || 0,
      // Total cost — required for pay_with_transfer Paystack initialization
      totalCost: totalCost,
    };

    if (mode === 'quick') {
      orderData.dropoff = dropoffAddress;
      orderData.receiverName = receiverName;
      orderData.receiverPhone = receiverPhone;
      orderData.packageType = drops[0]?.pkg || 'Box';
    } else if (mode === 'multi' || mode === 'bulk') {
      orderData.deliveries = deliveries.map((d: any) => ({
        dropoff_address: d.address,
        receiver_name: d.name,
        receiver_phone: d.phone,
        package_type: d.pkg || 'Box',
        notes: d.notes || ''
      }));
    }

    setSubmitting(true);
    try {
      await onPlaceOrder(orderData);
    } finally {
      setSubmitting(false);
    }
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

            {mode === "quick" && (
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 8 }}>Deliver To</label>
                <AddressAutocompleteInput
                  value={dropoffAddress}
                  onChange={setDropoffAddress}
                  placeholder="Enter dropoff address"
                  style={{
                    width: "100%", height: 48, padding: "0 16px", borderRadius: 10, fontSize: 14,
                    border: sameAddressError === "same-quick" ? "1.5px solid #ef4444" : "1.5px solid #e2e8f0"
                  }}
                />

                {/* Same-address error banner */}
                {sameAddressError === "same-quick" && (
                  <div style={{
                    marginTop: 8, padding: "10px 14px",
                    background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10,
                    display: "flex", alignItems: "flex-start", gap: 10
                  }}>
                    <span style={{ fontSize: 16, flexShrink: 0 }}>🚧</span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "#b91c1c", marginBottom: 2 }}>Pickup &amp; dropoff can&apos;t be the same address</div>
                      <div style={{ fontSize: 11, color: "#dc2626" }}>Please enter a different delivery destination.</div>
                    </div>
                  </div>
                )}

                {routeError && !sameAddressError && <div style={{ color: S.red, fontSize: 12, marginTop: 4 }}>{routeError}</div>}
                {calculatingRoute && !sameAddressError && <div style={{ color: S.gold, fontSize: 12, marginTop: 4 }}>Computing route...</div>}

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
                  <input value={receiverName} onChange={e => setReceiverName(e.target.value)} placeholder="Receiver Name" style={{ height: 44, padding: "0 14px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
                  <input value={receiverPhone} onChange={e => setReceiverPhone(e.target.value)} placeholder="Receiver Phone" style={{ height: 44, padding: "0 14px", borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14 }} />
                </div>
                <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Delivery instructions (optional)" style={{ width: "100%", height: 80, padding: 14, borderRadius: 10, border: "1.5px solid #e2e8f0", fontSize: 14, marginTop: 12, fontFamily: "inherit", resize: "none" }} />
              </div>
            )}

            {/* MULTI MODE */}
            {mode === "multi" && (
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.navy, marginBottom: 8 }}>Drop-off Locations</label>
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  {drops.map((drop, i) => {
                    const isSameAsPickup = !!pickupAddress && !!drop.address && normaliseAddr(pickupAddress) === normaliseAddr(drop.address);
                    return (
                      <div key={drop.id} style={{ border: `1.5px solid ${isSameAsPickup ? "#fecaca" : "#e2e8f0"}`, borderRadius: 10, padding: 16, position: "relative", background: isSameAsPickup ? "#fef9f9" : "#fff" }}>
                        <div style={{ position: "absolute", top: 16, left: 16, width: 24, height: 24, borderRadius: "50%", background: S.gold, color: S.navy, fontSize: 12, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>{i + 1}</div>
                        {drops.length > 1 && (
                          <button onClick={() => removeDrop(drop.id)} style={{ position: "absolute", top: 16, right: 16, background: "none", border: "none", color: S.red, cursor: "pointer", fontSize: 18 }}>×</button>
                        )}
                        <div style={{ marginLeft: 36 }}>
                          <AddressAutocompleteInput
                            value={drop.address}
                            onChange={(val) => updateDrop(drop.id, "address", val)}
                            placeholder="Dropoff address"
                            style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: `1px solid ${isSameAsPickup ? "#ef4444" : "#cbd5e1"}`, fontSize: 14, marginBottom: isSameAsPickup ? 8 : 12 }}
                          />
                          {isSameAsPickup && (
                            <div style={{
                              marginBottom: 12, padding: "8px 12px",
                              background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
                              display: "flex", alignItems: "center", gap: 8
                            }}>
                              <span style={{ fontSize: 14 }}>🚧</span>
                              <div style={{ fontSize: 12, fontWeight: 700, color: "#b91c1c" }}>This address is the same as your pickup — please choose a different destination.</div>
                            </div>
                          )}
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                            <input value={drop.name} onChange={(e) => updateDrop(drop.id, "name", e.target.value)} placeholder="Receiver Name" style={{ height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }} />
                            <input value={drop.phone} onChange={(e) => updateDrop(drop.id, "phone", e.target.value)} placeholder="Receiver Phone" style={{ height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
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
                {Object.keys(vehiclePricing).map(vName => {
                  const isComingSoon = vName === 'Car' || vName === 'Van';
                  const isSelected = vehicle === vName && !isComingSoon;
                  const earlyP = (mode === 'quick' && earlyRouteDistance)
                    ? calcTieredPrice(earlyRouteDistance, vehiclePricing[vName]?.pricing_tiers) ??
                    Math.round((vehiclePricing[vName]?.base_fare || 0) + earlyRouteDistance * (vehiclePricing[vName]?.rate_per_km || 0) + (earlyRouteDuration || 0) * (vehiclePricing[vName]?.rate_per_minute || 0))
                    : null;

                  return (
                    <button
                      key={vName}
                      onClick={() => !isComingSoon && setVehicle(vName)}
                      disabled={isComingSoon}
                      style={{
                        display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: 16,
                        borderRadius: 12,
                        border: isSelected ? `2px solid ${S.gold}` : "1px solid #e2e8f0",
                        background: isSelected ? S.goldPale : "#fff",
                        cursor: isComingSoon ? "not-allowed" : "pointer",
                        transition: "all 0.2s",
                        opacity: isComingSoon ? 0.7 : 1,
                        position: "relative"
                      }}
                    >
                      {isComingSoon && (
                        <div style={{
                          position: "absolute", top: 6, right: 6,
                          background: "#e2e8f0", color: "#64748b",
                          fontSize: 8, fontWeight: 700, padding: "2px 5px",
                          borderRadius: 4, textTransform: "uppercase" as const, letterSpacing: 0.3
                        }}>Soon</div>
                      )}
                      <div style={{ color: isSelected ? S.navy : S.gray }}>
                        {vName === 'Bike' ? Icons.bike : vName === 'Car' ? Icons.car : Icons.van}
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 600, color: isComingSoon ? S.grayLight : S.navy }}>{vName}</span>
                      {earlyP != null && (
                        <span style={{ fontSize: 11, color: isComingSoon ? S.grayLight : S.gold, fontWeight: 700 }}>
                          ₦{earlyP.toLocaleString()}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* ── Sticky bottom: Summary + Continue ── */}
            <div style={{
              background: "#fff", borderRadius: 14, border: `2px solid ${canProceed ? S.gold : "#e2e8f0"}`,
              padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
              transition: "all 0.3s"
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ fontSize: 13, color: S.gray }}>
                    <span style={{ fontWeight: 700, color: S.navy, fontSize: 20, fontFamily: "'Space Mono', monospace" }}>{totalDeliveries}</span>
                    <span style={{ marginLeft: 4 }}>{totalDeliveries === 1 ? "delivery" : "deliveries"}</span>
                  </div>
                  {totalDeliveries > 0 && (
                    <div style={{ width: 1, height: 24, background: "#e2e8f0" }} />
                  )}
                  {totalDeliveries > 0 && (
                    <div>
                      <div style={{ fontSize: 11, color: S.grayLight }}>Estimated Total</div>
                      <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>
                        ₦{(mode === 'quick' && pickupAddress && dropoffAddress && calculatingRoute && !earlyRouteDistance) ? '—' : totalCost.toLocaleString()}
                      </div>
                    </div>
                  )}
                </div>
                {totalDeliveries > 1 && (
                  <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>
                    ₦{unitCost.toLocaleString()} × {totalDeliveries} deliveries
                  </div>
                )}
              </div>

              <button
                onClick={() => setStep(2)}
                disabled={!canProceed}
                style={{
                  padding: "14px 32px", borderRadius: 12, border: "none", fontSize: 15, fontWeight: 700, cursor: canProceed ? "pointer" : "default",
                  background: canProceed ? `linear-gradient(135deg, ${S.gold}, ${S.gold})` : "#e2e8f0",
                  color: canProceed ? S.navy : "#94a3b8", fontFamily: "inherit",
                  boxShadow: canProceed ? "0 4px 12px rgba(232,168,56,0.3)" : "none",
                  transition: "all 0.2s"
                }}>
                Review & Pay →
              </button>
            </div>
            {showProceedErrors && (
              <div style={{
                marginTop: 10,
                padding: '10px 14px',
                borderRadius: 12,
                border: '1px solid #fecaca',
                background: '#fef2f2',
                color: '#991b1b',
                fontSize: 12,
                fontWeight: 600
              }}>
                <div style={{ marginBottom: 6 }}>Please complete the required fields:</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {proceedErrors.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            )}
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
                <button onClick={() => setPayMethod('pay_with_transfer')} style={{ flex: 1, padding: 12, border: payMethod === 'pay_with_transfer' ? `2px solid ${S.navy}` : '1px solid #e2e8f0', borderRadius: 10, background: payMethod === 'pay_with_transfer' ? '#f8fafc' : '#fff', textAlign: "left", cursor: "pointer" }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: S.navy, display: "flex", alignItems: "center", gap: 8 }}>
                    🏛️ Bank Transfer
                  </div>
                  <div style={{ fontSize: 12, color: S.gray, marginTop: 4 }}>Paystack Transfer</div>
                </button>
                <button onClick={() => setPayMethod('receiver_pays')} style={{ flex: 1, padding: 12, border: payMethod === 'receiver_pays' ? `2px solid ${S.navy}` : '1px solid #e2e8f0', borderRadius: 10, background: payMethod === 'receiver_pays' ? '#f8fafc' : '#fff', textAlign: "left", cursor: "pointer" }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: S.navy, display: "flex", alignItems: "center", gap: 8 }}>
                    🤝 Receiver Pays
                  </div>
                  <div style={{ fontSize: 12, color: S.gray, marginTop: 4 }}>Pay on delivery</div>
                </button>
              </div>
            </div>

            {/* Total */}
            <div style={{ background: S.navy, padding: 20, borderRadius: 12, color: "#fff" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <span style={{ opacity: 0.8, fontSize: 13 }}>Total Cost</span>
                <span style={{ fontSize: 20, fontWeight: 700 }}>₦{totalCost.toLocaleString()}</span>
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
                disabled={submitting || (payMethod === 'wallet' && totalCost > balance)}
                style={{
                  flex: 2, padding: 16, borderRadius: 12, border: "none",
                  background: (payMethod === 'wallet' && totalCost > balance) ? '#e2e8f0' : S.navy,
                  color: (payMethod === 'wallet' && totalCost > balance) ? '#94a3b8' : '#fff',
                  fontWeight: 700, cursor: (payMethod === 'wallet' && totalCost > balance) ? "not-allowed" : "pointer"
                }}
              >
                {(payMethod === 'wallet' && totalCost > balance) ? 'Insufficient Funds' : (payMethod === 'pay_with_transfer' ? (submitting ? 'Initializing...' : 'Pay & Confirm') : (submitting ? 'Confirming...' : 'Confirm Order'))}
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
          totalCost={totalCost}
          onRouteCalculated={(dist: number, time: number) => {
            setRouteDistance(dist);
            setRouteDuration(time);
          }}
        />
      </div>
    </div>
  );
}
