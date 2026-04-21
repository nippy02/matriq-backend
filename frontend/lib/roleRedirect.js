export function getRedirectByRole(role) {
  switch (role) {
    case 'Administrator':
      return '/admin';
    case 'QA Engineer':
    case 'Lab Technician':
    case 'Senior Technician':
      return '/technical';
    case 'Accounting Staff':
      return '/accounting';
    default:
      return '/auth/access-select';
  }
}
