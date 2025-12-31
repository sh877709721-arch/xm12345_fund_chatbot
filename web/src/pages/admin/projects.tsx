export default function Projects() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Projects</h1>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Current Projects</h2>
        <ul className="list-disc pl-5 space-y-2">
          <li>Data Analysis Dashboard Redesign</li>
          <li>Mobile App Development</li>
          <li>Customer Segmentation Study</li>
          <li>Market Research Initiative</li>
        </ul>
      </div>
      <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Project Status</h2>
        <p className="text-gray-600">All projects are on track for their deadlines.</p>
      </div>
    </div>
  );
}