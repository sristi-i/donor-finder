// app/donors/[id]/page.tsx
import { fetchDonorDetail } from "@/app/lib/api";
import DonorProfile from "@/app/components/DonorProfile";

type Params = Promise<{ id: string }>;
export const dynamic = "force-dynamic";

export default async function DonorDetailPage({ params }: { params: Params }) {
  const { id } = await params;
  const donorId = Number(id);
  const data = await fetchDonorDetail(donorId);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <a href="/donors" className="text-sm text-blue-600 underline">&larr; Back to list</a>
      <DonorProfile data={data} />
    </div>
  );
}
