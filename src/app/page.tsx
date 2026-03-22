import Link from "next/link";

export default function Home() {
  return (
    <div className="text-center py-12">
      <h1 className="text-4xl font-bold mb-4">Family Chore Tracker</h1>
      <p className="text-gray-600 mb-8 text-lg">
        Track chores, log your work, and get paid!
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
        <Link
          href="/chores"
          className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition"
        >
          <h2 className="text-xl font-semibold mb-2">Manage Chores</h2>
          <p className="text-gray-500">Add, remove, and view all available chores</p>
        </Link>
        <Link
          href="/log"
          className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition"
        >
          <h2 className="text-xl font-semibold mb-2">Weekly Log</h2>
          <p className="text-gray-500">Log the chores you&apos;ve completed this week</p>
        </Link>
        <Link
          href="/dashboard"
          className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition"
        >
          <h2 className="text-xl font-semibold mb-2">Dad&apos;s Dashboard</h2>
          <p className="text-gray-500">Review work and assign payouts</p>
        </Link>
      </div>
    </div>
  );
}
