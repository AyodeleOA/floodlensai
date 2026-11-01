import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <h1 className="text-4xl font-bold text-slate-900">404</h1>
      <p className="mt-2 text-slate-600">This page could not be found.</p>
      <Link to="/" className="btn-primary mt-6">
        <Home className="h-4 w-4" />
        Go Home
      </Link>
    </div>
  );
}
