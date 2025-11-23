import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import type { Profile } from '../../types/api';

interface ProfileSelectorProps {
  onProfileSelected: (profileName: string) => void;
  selectedProfile: string;
}

export function ProfileSelector({ onProfileSelected, selectedProfile }: ProfileSelectorProps) {
  const { data: profiles = [], isLoading, error } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiClient.getProfiles(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Loading profiles...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{(error as Error).message}</p>
      </div>
    );
  }

  if (profiles.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 mb-4">No profiles available</p>
        <a
          href="/profiles"
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Create a profile first
        </a>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {profiles.map((profile: Profile) => (
        <div
          key={profile.profile_name}
          onClick={() => onProfileSelected(profile.profile_name)}
          className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
            selectedProfile === profile.profile_name
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300 bg-white'
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`w-5 h-5 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${
                selectedProfile === profile.profile_name
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300'
              }`}
            >
              {selectedProfile === profile.profile_name && (
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900">{profile.profile_name}</h3>
              {profile.description && (
                <p className="text-sm text-gray-600 mt-1">{profile.description}</p>
              )}
              <div className="mt-2 text-xs text-gray-500">
                {(profile.mappings || []).length} mappings
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
