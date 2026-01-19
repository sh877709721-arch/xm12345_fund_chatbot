export default function Lifecycle() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Product Lifecycle</h1>
      <div className="bg-background dark:bg-background p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Current Stage: Growth</h2>
        <p className="text-gray-600 mb-4">
          The product is experiencing rapid growth with increasing user adoption
          and market penetration.
        </p>
        <div className="flex items-center">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600 w-3/4"></div>
          </div>
          <span className="ml-4 text-sm font-medium text-gray-600">
            75% Complete
          </span>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-background dark:bg-background p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-2">Introduction</h3>
          <p className="text-gray-600 text-sm">Completed</p>
        </div>
        <div className="bg-background dark:bg-background p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-2">Growth</h3>
          <p className="text-gray-600 text-sm">In Progress</p>
        </div>
        <div className="bg-background dark:bg-background p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-2">Maturity</h3>
          <p className="text-gray-600 text-sm">Upcoming</p>
        </div>
      </div>
    </div>
  );
}
