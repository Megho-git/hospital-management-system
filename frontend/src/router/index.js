import { createRouter, createWebHistory } from 'vue-router'
import { store } from '@/store'

import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import AdminDashboard from '@/views/admin/Dashboard.vue'
import AdminDoctors from '@/views/admin/Doctors.vue'
import AdminPatients from '@/views/admin/Patients.vue'
import AdminAppointments from '@/views/admin/Appointments.vue'
import AdminDepartments from '@/views/admin/Departments.vue'
import AdminMedications from '@/views/admin/Medications.vue'
import AdminLabTests from '@/views/admin/LabTests.vue'
import AdminBilling from '@/views/admin/Billing.vue'
import AdminInvoicePrint from '@/views/admin/InvoicePrint.vue'
import AdminAuditLog from '@/views/admin/AuditLog.vue'
import AdminAnalytics from '@/views/admin/Analytics.vue'
import DoctorDashboard from '@/views/doctor/Dashboard.vue'
import DoctorAvailability from '@/views/doctor/Availability.vue'
import DoctorPatientHistory from '@/views/doctor/PatientHistory.vue'
import DoctorPatientTimeline from '@/views/doctor/PatientTimeline.vue'
import DoctorProfile from '@/views/doctor/Profile.vue'
import AdminProfile from '@/views/admin/Profile.vue'
import PatientDashboard from '@/views/patient/Dashboard.vue'
import PatientHealthDashboard from '@/views/patient/HealthDashboard.vue'
import PatientDepartments from '@/views/patient/Departments.vue'
import PatientDoctorProfile from '@/views/patient/DoctorProfile.vue'
import PatientBookAppointment from '@/views/patient/BookAppointment.vue'
import PatientHistory from '@/views/patient/History.vue'
import PatientProfile from '@/views/patient/Profile.vue'
import PatientAppointmentSummary from '@/views/patient/AppointmentSummary.vue'
import PatientVitals from '@/views/patient/Vitals.vue'
import PatientLabResults from '@/views/patient/LabResults.vue'
import PatientBilling from '@/views/patient/Billing.vue'
import PatientInvoicePrint from '@/views/patient/InvoicePrint.vue'
import PatientDocuments from '@/views/patient/Documents.vue'
import NotFound from '@/views/NotFound.vue'
import TelemedicineRoom from '@/views/TelemedicineRoom.vue'
import PatientRpmVitals from '@/views/patient/RpmVitals.vue'
import AdminInventory from '@/views/admin/Inventory.vue'
import PatientPrescriptions from '@/views/patient/Prescriptions.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login, meta: { guest: true } },
  { path: '/register', component: Register, meta: { guest: true } },
  { path: '/admin', component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/doctors', component: AdminDoctors, meta: { role: 'admin' } },
  { path: '/admin/patients', component: AdminPatients, meta: { role: 'admin' } },
  { path: '/admin/appointments', component: AdminAppointments, meta: { role: 'admin' } },
  { path: '/admin/departments', component: AdminDepartments, meta: { role: 'admin' } },
  { path: '/admin/medications', component: AdminMedications, meta: { role: 'admin' } },
  { path: '/admin/lab-tests', component: AdminLabTests, meta: { role: 'admin' } },
  { path: '/admin/billing', component: AdminBilling, meta: { role: 'admin' } },
  { path: '/admin/invoices/:id/print', component: AdminInvoicePrint, meta: { role: 'admin' } },
  { path: '/admin/audit-log', component: AdminAuditLog, meta: { role: 'admin' } },
  { path: '/admin/analytics', component: AdminAnalytics, meta: { role: 'admin' } },
  { path: '/admin/inventory', component: AdminInventory, meta: { role: 'admin' } },
  { path: '/admin/profile', component: AdminProfile, meta: { role: 'admin' } },
  { path: '/doctor', component: DoctorDashboard, meta: { role: 'doctor' } },
  { path: '/doctor/availability', component: DoctorAvailability, meta: { role: 'doctor' } },
  { path: '/doctor/patients/:id/history', component: DoctorPatientHistory, meta: { role: 'doctor' } },
  { path: '/doctor/patients/:id/timeline', component: DoctorPatientTimeline, meta: { role: 'doctor' } },
  { path: '/doctor/profile', component: DoctorProfile, meta: { role: 'doctor' } },
  { path: '/patient', component: PatientDashboard, meta: { role: 'patient' } },
  { path: '/patient/health', component: PatientHealthDashboard, meta: { role: 'patient' } },
  { path: '/patient/departments', component: PatientDepartments, meta: { role: 'patient' } },
  { path: '/patient/doctors/:id', component: PatientDoctorProfile, meta: { role: 'patient' } },
  { path: '/patient/book/:doctorId', component: PatientBookAppointment, meta: { role: 'patient' } },
  { path: '/patient/appointments/:id/summary', component: PatientAppointmentSummary, meta: { role: 'patient' } },
  { path: '/patient/history', component: PatientHistory, meta: { role: 'patient' } },
  { path: '/patient/vitals', component: PatientVitals, meta: { role: 'patient' } },
  { path: '/patient/lab-results', component: PatientLabResults, meta: { role: 'patient' } },
  { path: '/patient/documents', component: PatientDocuments, meta: { role: 'patient' } },
  { path: '/patient/trends', component: PatientRpmVitals, meta: { role: 'patient' } },
  { path: '/patient/prescriptions', component: PatientPrescriptions, meta: { role: 'patient' } },
  { path: '/patient/billing', component: PatientBilling, meta: { role: 'patient' } },
  { path: '/patient/invoices/:id/print', component: PatientInvoicePrint, meta: { role: 'patient' } },
  { path: '/patient/profile', component: PatientProfile, meta: { role: 'patient' } },
  { path: '/telemedicine/appointments/:id', component: TelemedicineRoom, meta: { role: null } },
  { path: '/:pathMatch(.*)*', component: NotFound, meta: { guest: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.guest) return next()
  if (!store.isLoggedIn) return next('/login')
  // role===null means "any authenticated role"
  if (to.meta.role && store.role !== to.meta.role) return next('/' + store.role)
  next()
})

export default router
