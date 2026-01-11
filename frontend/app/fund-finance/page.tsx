"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Wallet,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Loader2,
  RefreshCw,
  Building,
  Users,
  ShieldCheck,
} from "lucide-react";
import {
  fetchFundFinanceSummary,
  fetchNAVFacilities,
  fetchLTV,
  fetchBufferAnalysis,
  checkILPACompliance,
  fetchLPTransparency,
  type NAVFacility,
  type LPPosition,
} from "@/lib/api";

interface FacilityDetails {
  facility: NAVFacility;
  ltv?: {
    current_ltv: number;
    max_ltv: number;
    buffer: number;
    status: string;
  };
  buffer?: {
    current_buffer: number;
    required_buffer: number;
    additional_borrowing_capacity: number;
  };
  ilpa?: {
    compliant: boolean;
    compliance_score: number;
    requirements_met: string[];
    requirements_failed: string[];
  };
  lp_transparency?: {
    lp_positions: LPPosition[];
    total_commitment: number;
    concentration_risk: string;
  };
  loading: boolean;
}

function getLTVStatus(ltv: number, maxLtv: number): string {
  const ratio = ltv / maxLtv;
  if (ratio < 0.7) return "GREEN";
  if (ratio < 0.9) return "AMBER";
  return "RED";
}

function getStatusColor(status: string): string {
  switch (status?.toUpperCase()) {
    case "GREEN":
    case "HEALTHY":
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "AMBER":
    case "WARNING":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "RED":
    case "CRITICAL":
      return "bg-red-100 text-red-800 border-red-200";
    default:
      return "bg-slate-100 text-slate-800 border-slate-200";
  }
}

export default function FundFinancePage() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<{
    total_facilities: number;
    total_nav: number;
    avg_ltv: number;
    ilpa_compliant_count: number;
  } | null>(null);
  const [facilities, setFacilities] = useState<NAVFacility[]>([]);
  const [selectedFacility, setSelectedFacility] = useState<string | null>(null);
  const [facilityDetails, setFacilityDetails] = useState<Map<string, FacilityDetails>>(new Map());
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [summaryRes, facilitiesRes] = await Promise.allSettled([
        fetchFundFinanceSummary(),
        fetchNAVFacilities(),
      ]);

      if (summaryRes.status === "fulfilled" && summaryRes.value.success) {
        setSummary({
          total_facilities: summaryRes.value.total_facilities,
          total_nav: summaryRes.value.total_nav,
          avg_ltv: summaryRes.value.avg_ltv,
          ilpa_compliant_count: summaryRes.value.ilpa_compliant_count,
        });
      }

      if (facilitiesRes.status === "fulfilled" && facilitiesRes.value.success) {
        setFacilities(facilitiesRes.value.facilities || []);
      }
    } catch (err) {
      console.error("Failed to load fund finance data:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadFacilityDetails(facilityId: string) {
    const existing = facilityDetails.get(facilityId);
    if (existing && !existing.loading) return;

    const facility = facilities.find((f) => f.facility_id === facilityId);
    if (!facility) return;

    setFacilityDetails((prev) => {
      const next = new Map(prev);
      next.set(facilityId, { facility, loading: true });
      return next;
    });

    try {
      const [ltvRes, bufferRes, ilpaRes, lpRes] = await Promise.allSettled([
        fetchLTV(facilityId),
        fetchBufferAnalysis(facilityId),
        checkILPACompliance(facilityId),
        fetchLPTransparency(facilityId),
      ]);

      setFacilityDetails((prev) => {
        const next = new Map(prev);
        next.set(facilityId, {
          facility,
          ltv: ltvRes.status === "fulfilled" && ltvRes.value.success ? {
            current_ltv: ltvRes.value.current_ltv,
            max_ltv: ltvRes.value.max_ltv,
            buffer: ltvRes.value.buffer,
            status: ltvRes.value.status,
          } : undefined,
          buffer: bufferRes.status === "fulfilled" && bufferRes.value.success ? {
            current_buffer: bufferRes.value.current_buffer,
            required_buffer: bufferRes.value.required_buffer,
            additional_borrowing_capacity: bufferRes.value.additional_borrowing_capacity,
          } : undefined,
          ilpa: ilpaRes.status === "fulfilled" && ilpaRes.value.success ? {
            compliant: ilpaRes.value.compliant,
            compliance_score: ilpaRes.value.compliance_score,
            requirements_met: ilpaRes.value.requirements_met,
            requirements_failed: ilpaRes.value.requirements_failed,
          } : undefined,
          lp_transparency: lpRes.status === "fulfilled" && lpRes.value.success ? {
            lp_positions: lpRes.value.lp_positions,
            total_commitment: lpRes.value.total_commitment,
            concentration_risk: lpRes.value.concentration_risk,
          } : undefined,
          loading: false,
        });
        return next;
      });
    } catch (err) {
      console.error("Failed to load facility details:", err);
      setFacilityDetails((prev) => {
        const next = new Map(prev);
        next.set(facilityId, { facility, loading: false });
        return next;
      });
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Fund Finance</h1>
            <p className="text-slate-500">
              NAV Facilities, LP Transparency & ILPA Compliance
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              ILPA July 2024 Guidance
            </Badge>
            <Button variant="outline" onClick={loadData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Building className="h-5 w-5 text-blue-500" />
                <p className="text-sm text-slate-500">NAV Facilities</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.total_facilities || facilities.length || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">Total NAV</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                ${((summary?.total_nav || 0) / 1e9).toFixed(2)}B
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-amber-500" />
                <p className="text-sm text-slate-500">Avg LTV</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {(summary?.avg_ltv || 0).toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">ILPA Compliant</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                {summary?.ilpa_compliant_count || 0}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">NAV Facilities</TabsTrigger>
            <TabsTrigger value="details">Facility Details</TabsTrigger>
            <TabsTrigger value="ilpa">ILPA Compliance</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">NAV Facility Portfolio</CardTitle>
              </CardHeader>
              <CardContent>
                {facilities.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Building className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>No NAV facilities found. Data loaded from BigQuery.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fund</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>NAV</TableHead>
                        <TableHead>Facility</TableHead>
                        <TableHead>LTV</TableHead>
                        <TableHead>Buffer</TableHead>
                        <TableHead>ILPA</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {facilities.map((facility) => (
                        <TableRow
                          key={facility.facility_id}
                          className="cursor-pointer hover:bg-slate-50"
                          onClick={() => {
                            setSelectedFacility(facility.facility_id);
                            loadFacilityDetails(facility.facility_id);
                            setActiveTab("details");
                          }}
                        >
                          <TableCell className="font-medium">
                            {facility.fund_name}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{facility.fund_type}</Badge>
                          </TableCell>
                          <TableCell>
                            ${(facility.nav_value / 1e6).toFixed(1)}M
                          </TableCell>
                          <TableCell>
                            ${(facility.facility_amount / 1e6).toFixed(1)}M
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress
                                value={Math.min(facility.ltv_ratio, 100)}
                                className="h-2 w-16"
                              />
                              <span className="text-sm">
                                {facility.ltv_ratio.toFixed(1)}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>{facility.buffer_percentage.toFixed(1)}%</TableCell>
                          <TableCell>
                            <Badge
                              className={
                                facility.ilpa_compliant
                                  ? "bg-emerald-100 text-emerald-800"
                                  : "bg-red-100 text-red-800"
                              }
                            >
                              {facility.ilpa_compliant ? "Compliant" : "Non-Compliant"}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Details Tab */}
          <TabsContent value="details">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Facility List */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-base">Select Facility</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                  {facilities.map((facility) => (
                    <div
                      key={facility.facility_id}
                      onClick={() => {
                        setSelectedFacility(facility.facility_id);
                        loadFacilityDetails(facility.facility_id);
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedFacility === facility.facility_id
                          ? "border-blue-500 bg-blue-50"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      <p className="font-medium text-slate-900">{facility.fund_name}</p>
                      <p className="text-xs text-slate-500">{facility.facility_id}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Facility Details */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">
                    {selectedFacility
                      ? `Facility Details - ${selectedFacility}`
                      : "Select a facility to view details"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedFacility ? (
                    (() => {
                      const details = facilityDetails.get(selectedFacility);
                      if (!details) return <p>Loading...</p>;
                      if (details.loading) {
                        return (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin" />
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-6">
                          {/* LTV Analysis */}
                          <div>
                            <h4 className="font-medium mb-3">LTV Analysis</h4>
                            {details.ltv ? (
                              <div className="grid grid-cols-3 gap-4">
                                <div className="p-3 bg-slate-50 rounded-lg">
                                  <p className="text-xs text-slate-500">Current LTV</p>
                                  <p className="text-xl font-bold">
                                    {details.ltv.current_ltv.toFixed(1)}%
                                  </p>
                                </div>
                                <div className="p-3 bg-slate-50 rounded-lg">
                                  <p className="text-xs text-slate-500">Max LTV</p>
                                  <p className="text-xl font-bold">
                                    {details.ltv.max_ltv.toFixed(1)}%
                                  </p>
                                </div>
                                <div className="p-3 bg-slate-50 rounded-lg">
                                  <p className="text-xs text-slate-500">Buffer</p>
                                  <p className="text-xl font-bold text-emerald-600">
                                    {details.ltv.buffer.toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                            ) : (
                              <p className="text-sm text-slate-500">No LTV data available</p>
                            )}
                          </div>

                          {/* Buffer Analysis */}
                          <div>
                            <h4 className="font-medium mb-3">Buffer Analysis</h4>
                            {details.buffer ? (
                              <div className="grid grid-cols-3 gap-4">
                                <div className="p-3 bg-slate-50 rounded-lg">
                                  <p className="text-xs text-slate-500">Current Buffer</p>
                                  <p className="text-xl font-bold">
                                    {details.buffer.current_buffer.toFixed(1)}%
                                  </p>
                                </div>
                                <div className="p-3 bg-slate-50 rounded-lg">
                                  <p className="text-xs text-slate-500">Required Buffer</p>
                                  <p className="text-xl font-bold">
                                    {details.buffer.required_buffer.toFixed(1)}%
                                  </p>
                                </div>
                                <div className="p-3 bg-slate-50 rounded-lg">
                                  <p className="text-xs text-slate-500">Add&apos;l Borrowing</p>
                                  <p className="text-xl font-bold text-blue-600">
                                    ${(details.buffer.additional_borrowing_capacity / 1e6).toFixed(1)}M
                                  </p>
                                </div>
                              </div>
                            ) : (
                              <p className="text-sm text-slate-500">No buffer data available</p>
                            )}
                          </div>

                          {/* LP Positions */}
                          <div>
                            <h4 className="font-medium mb-3">LP Transparency</h4>
                            {details.lp_transparency?.lp_positions?.length ? (
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead>LP Name</TableHead>
                                    <TableHead>Commitment</TableHead>
                                    <TableHead>Funded</TableHead>
                                    <TableHead>Concentration</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {details.lp_transparency.lp_positions.slice(0, 5).map((lp) => (
                                    <TableRow key={lp.lp_id}>
                                      <TableCell className="font-medium">{lp.lp_name}</TableCell>
                                      <TableCell>${(lp.commitment_amount / 1e6).toFixed(1)}M</TableCell>
                                      <TableCell>${(lp.funded_amount / 1e6).toFixed(1)}M</TableCell>
                                      <TableCell>
                                        <Badge
                                          className={
                                            lp.concentration_pct > 25
                                              ? "bg-amber-100 text-amber-800"
                                              : "bg-slate-100 text-slate-800"
                                          }
                                        >
                                          {lp.concentration_pct.toFixed(1)}%
                                        </Badge>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            ) : (
                              <p className="text-sm text-slate-500">No LP data available</p>
                            )}
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Users className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a facility from the list to view details</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ILPA Compliance Tab */}
          <TabsContent value="ilpa">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ShieldCheck className="h-5 w-5 text-blue-500" />
                  ILPA NAV Facility Guidance (July 2024)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {facilities.map((facility) => {
                    const details = facilityDetails.get(facility.facility_id);
                    return (
                      <div
                        key={facility.facility_id}
                        className={`p-4 rounded-lg border ${
                          facility.ilpa_compliant
                            ? "bg-emerald-50 border-emerald-200"
                            : "bg-red-50 border-red-200"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {facility.ilpa_compliant ? (
                              <CheckCircle className="h-5 w-5 text-emerald-600" />
                            ) : (
                              <AlertTriangle className="h-5 w-5 text-red-600" />
                            )}
                            <span className="font-medium">{facility.fund_name}</span>
                          </div>
                          <Badge
                            className={
                              facility.ilpa_compliant
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-red-100 text-red-800"
                            }
                          >
                            {facility.ilpa_compliant ? "ILPA Compliant" : "Non-Compliant"}
                          </Badge>
                        </div>
                        {details?.ilpa && (
                          <div className="mt-2">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm text-slate-600">Compliance Score:</span>
                              <Progress
                                value={details.ilpa.compliance_score}
                                className="h-2 w-32"
                              />
                              <span className="text-sm font-medium">
                                {details.ilpa.compliance_score}%
                              </span>
                            </div>
                            {details.ilpa.requirements_met.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {details.ilpa.requirements_met.map((req) => (
                                  <Badge
                                    key={req}
                                    variant="outline"
                                    className="text-xs bg-emerald-50"
                                  >
                                    ✓ {req}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                        {!details?.ilpa && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => loadFacilityDetails(facility.facility_id)}
                            className="mt-2"
                          >
                            Load Details
                          </Button>
                        )}
                      </div>
                    );
                  })}
                  {facilities.length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                      <ShieldCheck className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>No facilities to check. Data loaded from BigQuery.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
