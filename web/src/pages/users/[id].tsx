import { useParams, Link } from "react-router-dom";

export default function User() {
  const { id } = useParams();

  return (
    <div>
      <h1>User Details</h1>
      <p>User ID: {id}</p>
      <Link to="/users">Back to Users</Link> | <Link to="/">Go Home</Link>
    </div>
  );
}