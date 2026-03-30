<template>
  <div class="page">
    <div class="container">
      <h1 class="page-title">Admin Dashboard</h1>
      <p class="page-subtitle">Manage donors, content and ML training</p>

      <!-- Tabs -->
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id"
          class="tab-btn" :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id">
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Analytics Tab -->
      <div v-if="activeTab === 'analytics'">
        <div v-if="analyticsLoading" class="spinner"></div>
        <template v-else-if="analytics">
          <div class="grid-4 analytics-kpi-grid" style="margin-bottom:28px">
            <div class="stat-card"><div class="stat-icon">🩸</div><div class="stat-value">{{ analytics.total_donors }}</div><div class="stat-label">Total Donors</div></div>
            <div class="stat-card"><div class="stat-icon">🫁</div><div class="stat-value">{{ analytics.total_recipients }}</div><div class="stat-label">Total Recipients</div></div>
            <div class="stat-card" style="border-color:var(--info)">
              <div class="stat-icon" style="background:var(--info-bg)">🏥</div>
              <div class="stat-value" style="color:var(--info)">{{ analytics.total_hospitals }}</div>
              <div class="stat-label">Total Hospitals</div>
            </div>
            <div class="stat-card" style="border-color:var(--accent)">
              <div class="stat-icon" style="background:#fef9c3">👥</div>
              <div class="stat-value" style="color:var(--accent)">{{ analytics.total_users }}</div>
              <div class="stat-label">Total Users</div>
            </div>
          </div>

          <div class="grid-2 analytics-charts-grid" style="margin-bottom:24px">
            <div class="card chart-card">
              <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
                <span>Users Increased (Day-by-Day)</span>
                <select v-model="selectedGrowthMonth" class="filter-select" style="min-width:160px">
                  <option v-for="opt in growthMonthOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <Line
                v-if="usersGrowthChart"
                :data="usersGrowthChart"
                :options="{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }"
              />
            </div>
            <div class="card chart-card">
              <div class="card-header">Number of Users by Role</div>
              <Bar
                v-if="usersByRoleChart"
                :data="usersByRoleChart"
                :options="{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }"
              />
            </div>
          </div>

          <div class="card" style="margin-bottom:24px">
            <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
              <div>
                <span>User Management</span>
                <span class="donor-count">Total: {{ usersTotal }}</span>
              </div>
              <div class="analytics-filters" style="display:flex;gap:8px;flex-wrap:wrap">
                <input v-model="usersFilter.search" class="filter-select" type="text" placeholder="Search name/email" style="min-width:220px" />
                <select v-model="usersFilter.role" class="filter-select">
                  <option value="">All Roles</option>
                  <option value="donor">Donor</option>
                  <option value="recipient">Recipient</option>
                  <option value="hospital">Hospital</option>
                  <option value="admin">Admin</option>
                </select>
                <select v-model="usersFilter.status" class="filter-select">
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="">All Status</option>
                </select>
                <button class="btn btn-sm btn-outline" @click="applyUserFilters">Apply</button>
                <button class="btn btn-sm btn-secondary" @click="resetUserFilters">Reset</button>
              </div>
            </div>
            <div v-if="usersLoading" class="spinner"></div>
            <div v-else class="table-wrapper">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(u, idx) in users" :key="u.id">
                    <td>{{ ((usersPage - 1) * usersPageSize) + idx + 1 }}</td>
                    <td>{{ u.full_name || '—' }}</td>
                    <td>{{ u.email }}</td>
                    <td><span class="badge badge-info">{{ u.role }}</span></td>
                    <td>
                      <span class="badge" :class="u.is_active ? 'badge-success' : 'badge-danger'">
                        {{ u.is_active ? 'active' : 'inactive' }}
                      </span>
                    </td>
                    <td>{{ formatDate(u.created_at) }}</td>
                    <td>
                      <button class="btn btn-sm btn-danger" :disabled="!u.is_active || deletingUserId === u.id" @click="deleteUser(u)">
                        {{ deletingUserId === u.id ? 'Deleting...' : 'Delete' }}
                      </button>
                    </td>
                  </tr>
                  <tr v-if="users.length === 0">
                    <td colspan="7" style="text-align:center;color:var(--text-muted)">No users found</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="pagination" v-if="usersTotalPages > 1">
              <button class="btn btn-sm btn-outline" :disabled="usersPage === 1" @click="goToUsersPage(usersPage - 1)">Prev</button>
              <span class="page-info">Page {{ usersPage }} of {{ usersTotalPages }}</span>
              <button class="btn btn-sm btn-outline" :disabled="usersPage === usersTotalPages" @click="goToUsersPage(usersPage + 1)">Next</button>
            </div>
          </div>

          <div v-if="usersLoadError" class="alert alert-warning" style="margin-top:12px">
            {{ usersLoadError }}
          </div>
        </template>
      </div>

      <!-- Donors Tab -->
      <div v-if="activeTab === 'donors'">
        <!-- Add Donor Card -->
        <div class="card" style="margin-bottom:24px">
          <div class="card-header">Add New Donor</div>
          <div v-if="addDonorMsg" :class="['alert', addDonorError ? 'alert-danger' : 'alert-success']">{{ addDonorMsg }}</div>
          <form @submit.prevent="submitAddDonor">
            <div class="form-row">
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="donorForm.full_name" type="text" required />
              </div>
              <div class="form-group">
                <label>Age</label>
                <input v-model.number="donorForm.age" type="number" required />
              </div>
              <div class="form-group">
                <label>Blood Group</label>
                <select v-model="donorForm.blood_group" required>
                  <option value="">Select Blood Group</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                </select>
              </div>
              <div class="form-group">
                <label>Location</label>
                <input v-model="donorForm.location" type="text" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Organs</label>
                <div class="checkbox-group">
                  <label><input type="checkbox" value="heart" v-model="donorForm.organs_selected"> Heart</label>
                  <label><input type="checkbox" value="lung" v-model="donorForm.organs_selected"> Lung</label>
                  <label><input type="checkbox" value="kidney" v-model="donorForm.organs_selected"> Kidney</label>
                  <label><input type="checkbox" value="liver" v-model="donorForm.organs_selected"> Liver</label>
                  <label><input type="checkbox" value="pancreas" v-model="donorForm.organs_selected"> Pancreas</label>
                  <label><input type="checkbox" value="cornea" v-model="donorForm.organs_selected"> Cornea</label>
                </div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Emergency Contact (Optional)</label>
                <input v-model="donorForm.emergency_contact" type="text" placeholder="+91 XXXXXXXXXX" />
              </div>
              <div class="form-group">
                <label>Medical History (Optional)</label>
                <textarea v-model="donorForm.medical_history" rows="2" placeholder="Any relevant medical details..."></textarea>
              </div>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="addDonorLoading">
              {{ addDonorLoading ? 'Adding...' : 'Add Donor' }}
            </button>
          </form>
        </div>

        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <span>All Donors</span>
              <span class="donor-count">Total: {{ donors.length }}</span>
            </div>
            <select v-model="statusFilter" class="filter-select">
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div v-if="donorsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Age</th>
                  <th>Blood</th>
                  <th>Location</th>
                  <th>Organs</th>
                  <th>Status</th>
                  <th>Registered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in donors" :key="d.id">
                  <td>{{ d.full_name }}</td>
                  <td>{{ d.age }}</td>
                  <td>{{ d.blood_group }}</td>
                  <td>{{ d.location }}</td>
                  <td>
                    <span class="badge badge-info" v-for="o in (d.organs_selected || []).slice(0,2)" :key="o">{{ o }}</span>
                    <span v-if="d.organs_selected?.length > 2" class="badge badge-info">+{{ d.organs_selected.length - 2 }}</span>
                  </td>
                  <td><span class="badge" :class="statusClass(d.status)">{{ d.status }}</span></td>
                  <td>{{ new Date(d.created_at).toLocaleDateString() }}</td>
                  <td>
                    <div class="action-btns">
                      <button class="btn btn-sm btn-outline" @click="openProfile('donor', d)">👁 View Profile</button>
                      <!-- Pending: Show Approve and Reject -->
                      <template v-if="d.status === 'pending'">
                        <button class="btn btn-sm btn-accent" @click="updateStatus(d.id, 'approved')">✓ Approve</button>
                        <button class="btn btn-sm btn-outline" @click="updateStatus(d.id, 'rejected')">✗ Reject</button>
                      </template>
                      <!-- Approved: Show only Reject -->
                      <template v-else-if="d.status === 'approved'">
                        <button class="btn btn-sm btn-outline" @click="updateStatus(d.id, 'rejected')">✗ Reject</button>
                      </template>
                      <!-- Rejected: Show Re-approve and Delete -->
                      <template v-else-if="d.status === 'rejected'">
                        <button class="btn btn-sm btn-accent" @click="updateStatus(d.id, 'approved')">↩️ Re-approve</button>
                        <button class="btn btn-sm btn-danger" @click="deleteDonor(d.id)">🗑️ Delete</button>
                      </template>
                    </div>
                  </td>
                </tr>
                <tr v-if="donors.length === 0">
                  <td colspan="8" style="text-align:center;color:var(--text-muted)">No donors found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Rejection Reason Modal -->
        <div v-if="rejectReasonModal" class="modal-overlay" @click.self="cancelReject">
          <div class="modal-dialog">
            <div class="modal-header">
              <h3>Reject Donor</h3>
              <button class="modal-close" @click="cancelReject">✕</button>
            </div>
            <div class="modal-body">
              <p style="margin-bottom:16px">Please provide a reason for rejecting this donor:</p>
              <textarea v-model="rejectReason" rows="4" placeholder="Enter rejection reason..." style="width:100%;padding:12px;border:2px solid #000;border-radius:4px;font-family:var(--font);resize:vertical"></textarea>
              <small style="display:block;margin-top:8px;color:var(--text-muted)">Maximum 500 characters</small>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline" @click="cancelReject">Cancel</button>
              <button class="btn btn-danger" @click="confirmReject">✗ Confirm Reject</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Recipients Tab -->
      <div v-if="activeTab === 'recipients'">
        <div class="card" style="margin-bottom:24px">
          <div class="card-header">Add New Recipient</div>
          <div v-if="addRecipientMsg" :class="['alert', addRecipientError ? 'alert-danger' : 'alert-success']">{{ addRecipientMsg }}</div>
          <form @submit.prevent="submitAddRecipient">
            <div class="form-row">
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="recipientForm.full_name" type="text" required />
              </div>
              <div class="form-group">
                <label>Age</label>
                <input v-model.number="recipientForm.age" type="number" min="10" max="100" required />
              </div>
              <div class="form-group">
                <label>Blood Group</label>
                <select v-model="recipientForm.blood_group" required>
                  <option value="">Select Blood Group</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                </select>
              </div>
              <div class="form-group">
                <label>Urgency</label>
                <select v-model="recipientForm.urgency" required>
                  <option value="standard">standard</option>
                  <option value="high">high</option>
                  <option value="urgent">urgent</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Status</label>
                <select v-model="recipientForm.status" required>
                  <option value="pending">pending</option>
                  <option value="approved">approved</option>
                  <option value="rejected">rejected</option>
                  <option value="matched">matched</option>
                  <option value="completed">completed</option>
                </select>
              </div>
              <div class="form-group">
                <label>Assign Hospital (Optional)</label>
                <select v-model="recipientForm.hospital_id">
                  <option value="">Unassigned</option>
                  <option v-for="h in hospitals" :key="`rh-${h.id}`" :value="h.id">{{ h.hospital_name }} ({{ h.city }})</option>
                </select>
              </div>
              <div class="form-group" style="grid-column: span 2;">
                <label>Medical Condition</label>
                <textarea v-model="recipientForm.medical_condition" rows="2" required></textarea>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Organs Needed</label>
                <div class="checkbox-group">
                  <label><input type="checkbox" value="Kidney" v-model="recipientForm.organ_needed"> Kidney</label>
                  <label><input type="checkbox" value="Liver" v-model="recipientForm.organ_needed"> Liver</label>
                  <label><input type="checkbox" value="Heart" v-model="recipientForm.organ_needed"> Heart</label>
                  <label><input type="checkbox" value="Lungs" v-model="recipientForm.organ_needed"> Lungs</label>
                  <label><input type="checkbox" value="Cornea" v-model="recipientForm.organ_needed"> Cornea</label>
                  <label><input type="checkbox" value="Pancreas" v-model="recipientForm.organ_needed"> Pancreas</label>
                </div>
              </div>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="addRecipientLoading">
              {{ addRecipientLoading ? 'Adding...' : 'Add Recipient' }}
            </button>
          </form>
        </div>

        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <span>All Recipients</span>
              <span class="donor-count">Total: {{ recipients.length }}</span>
            </div>
            <select v-model="recipientStatusFilter" class="filter-select">
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="matched">Matched</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div v-if="recipientsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Age</th>
                  <th>Blood</th>
                  <th>Condition</th>
                  <th>Organs Needed</th>
                  <th>Urgency</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in recipients" :key="r.id">
                  <td>{{ r.full_name }}</td>
                  <td>{{ r.age }}</td>
                  <td>{{ r.blood_group }}</td>
                  <td class="truncate" :title="r.medical_condition">{{ r.medical_condition }}</td>
                  <td>
                    <span class="badge badge-info" v-for="o in (r.organ_needed || []).slice(0,2)" :key="o">{{ o }}</span>
                    <span v-if="r.organ_needed?.length > 2" class="badge badge-info">+{{ r.organ_needed.length - 2 }}</span>
                  </td>
                  <td>
                    <select class="filter-select" :value="r.urgency" @change="setRecipientUrgency(r, $event.target.value)">
                      <option value="standard">standard</option>
                      <option value="high">high</option>
                      <option value="urgent">urgent</option>
                    </select>
                  </td>
                  <td><span class="badge badge-info">{{ r.status }}</span></td>
                  <td>
                    <div class="action-btns">
                      <button class="btn btn-sm btn-outline" @click="openProfile('recipient', r)">👁 View Profile</button>
                      <button class="btn btn-sm btn-accent" @click="updateRecipientStatus(r.id, 'approved')">✓ Approve</button>
                      <button class="btn btn-sm btn-outline" @click="updateRecipientStatus(r.id, 'rejected')">✗ Reject</button>
                      <button class="btn btn-sm btn-danger" @click="deleteRecipient(r.id)">🗑️ Delete</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="recipients.length === 0">
                  <td colspan="8" style="text-align:center;color:var(--text-muted)">No recipients found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      

      <!-- Hospitals Tab -->
      <div v-if="activeTab === 'hospitals'">
        <div class="card" style="margin-bottom:24px">
          <div class="card-header">Add New Hospital</div>
          <div v-if="addHospitalMsg" :class="['alert', addHospitalError ? 'alert-danger' : 'alert-success']">{{ addHospitalMsg }}</div>
          <form @submit.prevent="submitAddHospital">
            <div class="form-row">
              <div class="form-group">
                <label>Hospital Name</label>
                <input v-model="hospitalForm.hospital_name" type="text" required />
              </div>
              <div class="form-group">
                <label>Registration Number</label>
                <input v-model="hospitalForm.registration_number" type="text" />
              </div>
              <div class="form-group">
                <label>City</label>
                <input v-model="hospitalForm.city" type="text" required />
              </div>
              <div class="form-group">
                <label>State</label>
                <input v-model="hospitalForm.state" type="text" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Phone</label>
                <input v-model="hospitalForm.phone" type="text" />
              </div>
              <div class="form-group">
                <label>Email</label>
                <input v-model="hospitalForm.email" type="email" />
              </div>
              <div class="form-group">
                <label>Website</label>
                <input v-model="hospitalForm.website" type="text" />
              </div>
              <div class="form-group">
                <label>Bed Capacity</label>
                <input v-model.number="hospitalForm.bed_capacity" type="number" min="0" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Specializations</label>
                <div class="checkbox-group">
                  <label><input type="checkbox" value="Kidney" v-model="hospitalForm.specializations"> Kidney</label>
                  <label><input type="checkbox" value="Liver" v-model="hospitalForm.specializations"> Liver</label>
                  <label><input type="checkbox" value="Heart" v-model="hospitalForm.specializations"> Heart</label>
                  <label><input type="checkbox" value="Lungs" v-model="hospitalForm.specializations"> Lungs</label>
                  <label><input type="checkbox" value="Pancreas" v-model="hospitalForm.specializations"> Pancreas</label>
                  <label><input type="checkbox" value="Cornea" v-model="hospitalForm.specializations"> Cornea</label>
                </div>
              </div>
              <div class="form-group" style="display:flex;align-items:center;gap:8px;margin-top:28px">
                <input id="hospital-verified" v-model="hospitalForm.is_verified" type="checkbox" />
                <label for="hospital-verified" style="margin:0">Mark as verified</label>
              </div>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="addHospitalLoading">
              {{ addHospitalLoading ? 'Adding...' : 'Add Hospital' }}
            </button>
          </form>
        </div>

        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <span>All Hospitals</span>
              <span class="donor-count">Total: {{ hospitals.length }}</span>
            </div>
            <select v-model="hospitalVerifiedFilter" class="filter-select">
              <option value="">All Verification</option>
              <option value="true">Verified</option>
              <option value="false">Unverified</option>
            </select>
          </div>
          <div v-if="hospitalsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Reg. No</th>
                  <th>City</th>
                  <th>State</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>Verified</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="h in hospitals" :key="h.id">
                  <td>{{ h.hospital_name }}</td>
                  <td>{{ h.registration_number }}</td>
                  <td>{{ h.city }}</td>
                  <td>{{ h.state }}</td>
                  <td>{{ h.phone }}</td>
                  <td class="truncate" :title="h.email">{{ h.email }}</td>
                  <td><span class="badge" :class="h.is_verified ? 'badge-success' : 'badge-warning'">{{ h.is_verified ? 'Verified' : 'Unverified' }}</span></td>
                  <td>
                    <div class="action-btns">
                      <button class="btn btn-sm btn-outline" @click="openProfile('hospital', h)">👁 View Profile</button>
                      <button class="btn btn-sm btn-accent" @click="updateHospitalStatus(h.id, 'approved')">✓ Approve</button>
                      <button class="btn btn-sm btn-outline" @click="updateHospitalStatus(h.id, 'suspended')">⏸ Suspend</button>
                      <button class="btn btn-sm btn-danger" @click="deleteHospital(h.id)">🗑️ Delete</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="hospitals.length === 0">
                  <td colspan="8" style="text-align:center;color:var(--text-muted)">No hospitals found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Profile Modal -->
      <div v-if="profileModal" class="modal-overlay" @click.self="closeProfile">
        <div class="modal-dialog modal-lg">
          <div class="modal-header">
            <h3>{{ profileTitle }}</h3>
            <button class="modal-close" @click="closeProfile">✕</button>
          </div>
          <div class="modal-body">
            <div class="profile-grid">
              <div class="profile-item" v-for="row in profileRows" :key="row.label">
                <div class="profile-item-label">{{ row.label }}</div>
                <div class="profile-item-value">{{ row.value }}</div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="closeProfile">Close</button>
          </div>
        </div>
      </div>

      <!-- ML Training Tab -->
      <div v-if="activeTab === 'ml'">
        <div class="card">
          <div class="card-header">ML Training Control</div>
          <div class="ml-status-box">
            <div class="ml-status-icon">{{ trainingStatus === 'completed' ? '✅' : trainingStatus === 'running' ? '⚙️' : trainingStatus === 'failed' ? '❌' : '🤖' }}</div>
            <div>
              <div class="ml-status-text">Status: <strong>{{ trainingStatus?.toUpperCase() || 'IDLE' }}</strong></div>
              <div v-if="lastTrained" class="ml-last">Last trained: {{ lastTrained }}</div>
            </div>
          </div>
          <div v-if="trainMsg" class="alert alert-success">{{ trainMsg }}</div>
          <button class="btn btn-primary btn-lg" @click="triggerTraining" :disabled="trainingStatus === 'running'">
            {{ trainingStatus === 'running' ? '⚙️ Training in progress...' : '🚀 Start ML Training' }}
          </button>
          <p class="ml-note">Training will process the Organ Donation CSV dataset and generate forecasts, ODII, and SHAP explanations. This may take 30–60 seconds.</p>
        </div>
      </div>

      <!-- System Logs Tab -->
      <div v-if="activeTab === 'system'">
        <div class="grid-2">
          <div class="card">
            <div class="card-header">🤖 LifeLink AI Chat Logs</div>
            <div v-if="logsLoading" class="spinner"></div>
            <div v-else class="table-wrapper">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Query</th>
                    <th>Topic</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in chatLogs" :key="log.id">
                    <td>User #{{ log.user_id }}</td>
                    <td class="truncate" :title="log.query">{{ log.query }}</td>
                    <td><span class="badge" :class="log.classification === 'organ_related' ? 'badge-success' : 'badge-warning'">{{ log.classification === 'organ_related' ? 'Organ' : 'Other' }}</span></td>
                    <td style="font-size:10px">{{ new Date(log.timestamp).toLocaleString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="card">
            <div class="card-header">📜 Model Version History</div>
            <div v-if="logsLoading" class="spinner"></div>
            <div v-else class="table-wrapper">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Accuracy</th>
                    <th>Trained At</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in modelVersions" :key="v.id">
                    <td style="font-weight:900">v{{ v.version_tag }}</td>
                    <td>{{ (v.accuracy * 100).toFixed(1) }}%</td>
                    <td>{{ new Date(v.training_date).toLocaleDateString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Tab -->
      <div v-if="activeTab === 'content'">
        <div class="card">
          <div class="card-header">Add Awareness Content</div>
          <div v-if="contentMsg" class="alert alert-success">{{ contentMsg }}</div>
          <form @submit.prevent="submitContent">
            <div class="form-group">
              <label>Title</label>
              <input v-model="contentForm.title" type="text" required />
            </div>
            <div class="form-group">
              <label>Type</label>
              <select v-model="contentForm.type" required>
                <option value="myth">Myth vs Fact</option>
                <option value="faq">FAQ</option>
                <option value="blog">Blog / Article</option>
                <option value="legal">Legal Info</option>
              </select>
            </div>
            <div class="form-group">
              <label>Content</label>
              <textarea v-model="contentForm.content" rows="5" required></textarea>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="contentLoading">
              {{ contentLoading ? 'Publishing...' : 'Publish Content' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement,
  Title, Tooltip, Legend
} from 'chart.js'
import api from '../services/api.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend)

const activeTab = ref('analytics')
const tabs = [
  { id: 'analytics', label: 'Analytics', icon: '📊' },
  { id: 'donors', label: 'Donors', icon: '👥' },
  { id: 'recipients', label: 'Recipients', icon: '🫁' },
  { id: 'hospitals', label: 'Hospitals', icon: '🏥' },
  { id: 'ml', label: 'ML Training', icon: '🤖' },
  { id: 'system', label: 'System Logs', icon: '📋' },
  { id: 'content', label: 'Content', icon: '📝' },
]

// Analytics
const analytics = ref(null)
const analyticsLoading = ref(false)
const users = ref([])
const usersLoading = ref(false)
const usersTotal = ref(0)
const usersPage = ref(1)
const usersPageSize = ref(10)
const usersTotalPages = ref(1)
const deletingUserId = ref(null)
const usersLoadError = ref('')
const usersFallbackMode = ref(false)
const usersChartSource = ref([])
const MIN_GROWTH_MONTH = '2026-03'
const selectedGrowthMonth = ref(new Date().toISOString().slice(0, 7))
const usersFilter = ref({
  role: '',
  status: 'active',
  search: '',
})

if (selectedGrowthMonth.value < MIN_GROWTH_MONTH) {
  selectedGrowthMonth.value = MIN_GROWTH_MONTH
}

const growthMonthOptions = computed(() => {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1
  const options = []

  for (let y = currentYear; y >= 2026; y--) {
    const startMonth = y === currentYear ? currentMonth : 12
    const endMonth = y === 2026 ? 3 : 1
    for (let m = startMonth; m >= endMonth; m--) {
      const value = `${y}-${String(m).padStart(2, '0')}`
      if (value < MIN_GROWTH_MONTH) continue
      const label = new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
      options.push({ value, label })
    }
  }

  return options
})

const usersGrowthChart = computed(() => {
  if (!usersChartSource.value.length) return null

  const [yearStr, monthStr] = selectedGrowthMonth.value.split('-')
  const year = Number(yearStr)
  const month = Number(monthStr)
  if (!year || !month) return null

  const daysInMonth = new Date(year, month, 0).getDate()
  const dayCounts = Array.from({ length: daysInMonth }, () => 0)

  usersChartSource.value.forEach((u) => {
    if (!u?.created_at) return
    const date = new Date(u.created_at)
    if (Number.isNaN(date.getTime())) return
    if (date.getFullYear() !== year || (date.getMonth() + 1) !== month) return
    const day = date.getDate()
    if (day >= 1 && day <= daysInMonth) {
      dayCounts[day - 1] += 1
    }
  })

  const monthLabel = new Date(year, month - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  return {
    labels: Array.from({ length: daysInMonth }, (_, i) => String(i + 1)),
    datasets: [{
      label: `New Users (${monthLabel})`,
      data: dayCounts,
      borderColor: '#ef4444',
      backgroundColor: 'rgba(239, 68, 68, 0.2)',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
    }],
  }
})

const usersByRoleChart = computed(() => {
  let byRole = analytics.value?.users_by_role
  if (!byRole && usersChartSource.value.length) {
    byRole = usersChartSource.value.reduce((acc, u) => {
      const role = u?.role || 'unknown'
      acc[role] = (acc[role] || 0) + 1
      return acc
    }, {})
  }
  if (!byRole) return null

  return {
    labels: Object.keys(byRole),
    datasets: [{
      label: 'Users',
      data: Object.values(byRole),
      backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
    }],
  }
})

// Donors
const donors = ref([])
const donorsLoading = ref(false)
const statusFilter = ref('')
const donorForm = ref({
  full_name: '',
  age: null,
  blood_group: '',
  location: '',
  organs_selected: [],
  medical_history: '',
  emergency_contact: '',
})
const addDonorLoading = ref(false)
const addDonorMsg = ref('')
const addDonorError = ref(false)
const rejectReasonModal = ref(false)
const rejectReason = ref('')
const rejectingDonorId = ref(null)

// Recipients
const recipients = ref([])
const recipientsLoading = ref(false)
const recipientStatusFilter = ref('')
const recipientForm = ref({
  full_name: '',
  age: null,
  blood_group: '',
  medical_condition: '',
  organ_needed: [],
  urgency: 'standard',
  status: 'pending',
  hospital_id: '',
})
const addRecipientLoading = ref(false)
const addRecipientMsg = ref('')
const addRecipientError = ref(false)

// Pending Recipient Verifications
const pendingRecipients = ref([])
const pendingVerificationsLoading = ref(false)
const recipientDetailsModal = ref(false)
const selectedRecipient = ref(null)
const rejectRecipientModal = ref(false)
const rejectRecipientReason = ref('')
const rejectingRecipientId = ref(null)

// Hospitals
const hospitals = ref([])
const hospitalsLoading = ref(false)
const hospitalVerifiedFilter = ref('')
const hospitalForm = ref({
  hospital_name: '',
  registration_number: '',
  city: '',
  state: '',
  phone: '',
  email: '',
  website: '',
  bed_capacity: null,
  specializations: [],
  is_verified: false,
})
const addHospitalLoading = ref(false)
const addHospitalMsg = ref('')
const addHospitalError = ref(false)

// Shared profile modal
const profileModal = ref(false)
const profileType = ref('')
const selectedProfile = ref(null)

// ML
const trainingStatus = ref('idle')
const lastTrained = ref(null)
const trainMsg = ref('')

// Content
const contentForm = ref({ title: '', type: 'myth', content: '' })
const contentMsg = ref('')
const contentLoading = ref(false)

// System Logs
const chatLogs = ref([])
const modelVersions = ref([])
const logsLoading = ref(false)

function statusClass(s) {
  return { pending: 'badge-warning', approved: 'badge-success', rejected: 'badge-danger' }[s] || 'badge-info'
}

async function loadAnalytics() {
  analyticsLoading.value = true
  try {
    const res = await api.get('/admin/analytics')
    analytics.value = res.data
    await loadUsers(1)
  } finally {
    analyticsLoading.value = false
  }
}

async function loadUsers(page = 1) {
  usersLoading.value = true
  usersLoadError.value = ''
  try {
    const params = {
      page,
      page_size: usersPageSize.value,
    }
    if (usersFilter.value.role) params.role = usersFilter.value.role
    if (usersFilter.value.status) params.status = usersFilter.value.status
    if (usersFilter.value.search?.trim()) params.q = usersFilter.value.search.trim()

    const res = await api.get('/admin/users', { params })
    usersFallbackMode.value = false
    users.value = res.data.items || []
    if (page === 1 && users.value.length) {
      usersChartSource.value = users.value
    }
    usersTotal.value = res.data.total || 0
    usersPage.value = res.data.page || 1
    usersTotalPages.value = res.data.total_pages || 1
  } catch (err) {
    const statusCode = err?.response?.status
    if (statusCode !== 404) {
      console.error('Failed to load users:', err)
      users.value = []
      usersTotal.value = 0
      usersPage.value = 1
      usersTotalPages.value = 1
    } else {
      usersFallbackMode.value = true
      usersLoadError.value = 'User API is not available on this server build. Showing users from donors/recipients/hospitals endpoints.'
      await loadUsersFallback(page)
    }
  } finally {
    usersLoading.value = false
  }
}

async function loadUsersFallback(page = 1) {
  const [donorRes, recipientRes, hospitalRes] = await Promise.all([
    api.get('/admin/donors', { params: { limit: 500 } }).catch(() => ({ data: [] })),
    api.get('/admin/recipients', { params: { limit: 500 } }).catch(() => ({ data: [] })),
    api.get('/admin/hospitals', { params: { limit: 500 } }).catch(() => ({ data: [] })),
  ])

  const donorUsers = (donorRes.data || []).map(d => ({
    id: `donor-${d.id}`,
    entity_id: d.id,
    role: 'donor',
    full_name: d.full_name,
    email: d.email || 'N/A',
    is_active: d.status !== 'rejected',
    created_at: d.created_at,
  }))

  console.log(donorRes.data)

  const recipientUsers = (recipientRes.data || []).map(r => ({
    id: `recipient-${r.id}`,
    entity_id: r.id,
    role: 'recipient',
    full_name: r.full_name,
    email: r.email || 'N/A',
    is_active: r.status !== 'rejected',
    created_at: r.created_at,
  }))

  const hospitalUsers = (hospitalRes.data || []).map(h => ({
    id: `hospital-${h.id}`,
    entity_id: h.id,
    role: 'hospital',
    full_name: h.hospital_name,
    email: h.email || 'N/A',
    is_active: !!h.is_verified,
    created_at: h.created_at,
  }))

  let merged = [...donorUsers, ...recipientUsers, ...hospitalUsers]
  usersChartSource.value = [...merged]

  if (usersFilter.value.role) {
    merged = merged.filter(u => u.role === usersFilter.value.role)
  }

  if (usersFilter.value.status === 'active') {
    merged = merged.filter(u => u.is_active)
  } else if (usersFilter.value.status === 'inactive') {
    merged = merged.filter(u => !u.is_active)
  }

  if (usersFilter.value.search?.trim()) {
    const q = usersFilter.value.search.trim().toLowerCase()
    merged = merged.filter(u =>
      (u.full_name || '').toLowerCase().includes(q) ||
      (u.email || '').toLowerCase().includes(q)
    )
  }

  merged.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))

  usersTotal.value = merged.length
  usersTotalPages.value = Math.max(1, Math.ceil(merged.length / usersPageSize.value))
  usersPage.value = Math.min(Math.max(1, page), usersTotalPages.value)

  const start = (usersPage.value - 1) * usersPageSize.value
  const end = start + usersPageSize.value
  users.value = merged.slice(start, end)
}

function applyUserFilters() {
  loadUsers(1)
}

function resetUserFilters() {
  usersFilter.value = {
    role: '',
    status: 'active',
    search: '',
  }
  loadUsers(1)
}

function goToUsersPage(page) {
  if (page < 1 || page > usersTotalPages.value) return
  loadUsers(page)
}

async function deleteUser(user) {
  if (!confirm(`Delete user ${user.email}? This will deactivate account access.`)) return
  deletingUserId.value = user.id
  try {
    if (!usersFallbackMode.value) {
      await api.delete(`/admin/users/${user.id}`)
    } else if (user.role === 'recipient') {
      await api.delete(`/admin/recipients/${user.entity_id || user.id.replace('recipient-', '')}`)
    } else if (user.role === 'hospital') {
      await api.delete(`/admin/hospitals/${user.entity_id || user.id.replace('hospital-', '')}`)
    } else if (user.role === 'donor') {
      await api.delete(`/donor/${user.entity_id || user.id.replace('donor-', '')}`)
    } else {
      throw new Error('Delete not supported for this user type in fallback mode')
    }

    if (users.length === 1 && usersPage.value > 1) {
      await loadUsers(usersPage.value - 1)
    } else {
      await loadUsers(usersPage.value)
    }
  } catch (err) {
    alert('Failed to delete user: ' + (err.response?.data?.detail || err.message))
  } finally {
    deletingUserId.value = null
  }
}

async function loadDonors() {
  donorsLoading.value = true
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : {}
    const res = await api.get('/admin/donors', { params })
    donors.value = res.data
  } finally {
    donorsLoading.value = false
  }
}

async function loadRecipients() {
  recipientsLoading.value = true
  try {
    const params = recipientStatusFilter.value ? { status: recipientStatusFilter.value } : {}
    const res = await api.get('/admin/recipients', { params })
    recipients.value = res.data
  } finally {
    recipientsLoading.value = false
  }
}

async function loadHospitals() {
  hospitalsLoading.value = true
  try {
    const params = {}
    if (hospitalVerifiedFilter.value === 'true') params.verified = true
    if (hospitalVerifiedFilter.value === 'false') params.verified = false
    const res = await api.get('/admin/hospitals', { params })
    hospitals.value = res.data
  } finally {
    hospitalsLoading.value = false
  }
}

async function submitAddRecipient() {
  addRecipientLoading.value = true
  addRecipientMsg.value = ''
  addRecipientError.value = false
  try {
    const payload = {
      full_name: recipientForm.value.full_name,
      age: recipientForm.value.age,
      blood_group: recipientForm.value.blood_group,
      medical_condition: recipientForm.value.medical_condition,
      organ_needed: recipientForm.value.organ_needed,
      urgency: recipientForm.value.urgency,
      status: recipientForm.value.status,
      hospital_id: recipientForm.value.hospital_id || null,
    }
    await api.post('/admin/recipients', payload)
    addRecipientMsg.value = 'Recipient added successfully!'
    recipientForm.value = {
      full_name: '',
      age: null,
      blood_group: '',
      medical_condition: '',
      organ_needed: [],
      urgency: 'standard',
      status: 'pending',
      hospital_id: '',
    }
    await loadRecipients()
  } catch (err) {
    addRecipientError.value = true
    addRecipientMsg.value = err.response?.data?.detail || 'Failed to add recipient'
  } finally {
    addRecipientLoading.value = false
  }
}

async function updateRecipientStatus(id, status) {
  try {
    await api.put(`/admin/recipients/${id}/status`, { status })
    await loadRecipients()
  } catch (err) {
    alert('Failed to update recipient status: ' + (err.response?.data?.detail || err.message))
  }
}

async function setRecipientUrgency(recipient, urgency) {
  try {
    await api.patch(`/admin/recipients/${recipient.id}/urgency`, { urgency })
    recipient.urgency = urgency
  } catch (err) {
    alert('Failed to update urgency: ' + (err.response?.data?.detail || err.message))
  }
}

async function deleteRecipient(id) {
  if (!confirm('Delete this recipient? This also removes linked organ requests.')) return
  try {
    await api.delete(`/admin/recipients/${id}`)
    await loadRecipients()
  } catch (err) {
    alert('Failed to delete recipient: ' + (err.response?.data?.detail || err.message))
  }
}

async function submitAddHospital() {
  addHospitalLoading.value = true
  addHospitalMsg.value = ''
  addHospitalError.value = false
  try {
    await api.post('/admin/hospitals', {
      hospital_name: hospitalForm.value.hospital_name,
      registration_number: hospitalForm.value.registration_number,
      city: hospitalForm.value.city,
      state: hospitalForm.value.state,
      phone: hospitalForm.value.phone,
      email: hospitalForm.value.email,
      website: hospitalForm.value.website,
      bed_capacity: hospitalForm.value.bed_capacity,
      specializations: hospitalForm.value.specializations,
      is_verified: hospitalForm.value.is_verified,
    })
    addHospitalMsg.value = 'Hospital created successfully!'
    hospitalForm.value = {
      hospital_name: '',
      registration_number: '',
      city: '',
      state: '',
      phone: '',
      email: '',
      website: '',
      bed_capacity: null,
      specializations: [],
      is_verified: false,
    }
    await loadHospitals()
  } catch (err) {
    addHospitalError.value = true
    addHospitalMsg.value = err.response?.data?.detail || 'Failed to add hospital'
  } finally {
    addHospitalLoading.value = false
  }
}

async function updateHospitalStatus(id, status) {
  try {
    await api.put(`/admin/hospitals/${id}/status`, { status })
    await loadHospitals()
  } catch (err) {
    alert('Failed to update hospital status: ' + (err.response?.data?.detail || err.message))
  }
}

async function deleteHospital(id) {
  if (!confirm('Delete this hospital? Linked recipients will be unassigned.')) return
  try {
    await api.delete(`/admin/hospitals/${id}`)
    await loadHospitals()
  } catch (err) {
    alert('Failed to delete hospital: ' + (err.response?.data?.detail || err.message))
  }
}

async function updateStatus(id, status) {
  if (status === 'rejected') {
    rejectingDonorId.value = id
    rejectReasonModal.value = true
  } else {
    await api.put(`/admin/donors/${id}/status`, { status })
    await loadDonors()
  }
}

async function confirmReject() {
  if (!rejectReason.value.trim()) {
    alert('Please provide a reason for rejection')
    return
  }
  try {
    await api.put(`/admin/donors/${rejectingDonorId.value}/status`, { 
      status: 'rejected',
      reason: rejectReason.value
    })
    rejectReasonModal.value = false
    rejectReason.value = ''
    rejectingDonorId.value = null
    await loadDonors()
  } catch (err) {
    alert('Failed to reject donor: ' + (err.response?.data?.detail || err.message))
  }
}

function cancelReject() {
  rejectReasonModal.value = false
  rejectReason.value = ''
  rejectingDonorId.value = null
}

function openProfile(type, item) {
  profileType.value = type
  selectedProfile.value = item
  profileModal.value = true
}

function closeProfile() {
  profileModal.value = false
  profileType.value = ''
  selectedProfile.value = null
}

const profileTitle = computed(() => {
  if (profileType.value === 'donor') return 'Donor Profile'
  if (profileType.value === 'recipient') return 'Recipient Profile'
  if (profileType.value === 'hospital') return 'Hospital Profile'
  return 'Profile'
})

const profileRows = computed(() => {
  const p = selectedProfile.value
  if (!p) return []

  if (profileType.value === 'donor') {
    return [
      { label: 'ID', value: p.id },
      { label: 'Full Name', value: p.full_name },
      { label: 'Age', value: p.age },
      { label: 'Blood Group', value: p.blood_group },
      { label: 'Location', value: p.location },
      { label: 'Organs Selected', value: (p.organs_selected || []).join(', ') || '-' },
      { label: 'Status', value: p.status },
      { label: 'Created At', value: p.created_at ? new Date(p.created_at).toLocaleString() : '-' },
    ]
  }

  if (profileType.value === 'recipient') {
    return [
      { label: 'ID', value: p.id },
      { label: 'User ID', value: p.user_id },
      { label: 'Full Name', value: p.full_name },
      { label: 'Age', value: p.age },
      { label: 'Blood Group', value: p.blood_group },
      { label: 'Medical Condition', value: p.medical_condition },
      { label: 'Organs Needed', value: (p.organ_needed || []).join(', ') || '-' },
      { label: 'Urgency', value: p.urgency },
      { label: 'Status', value: p.status },
      { label: 'Hospital ID', value: p.hospital_id || '-' },
      { label: 'Created At', value: p.created_at ? new Date(p.created_at).toLocaleString() : '-' },
    ]
  }

  if (profileType.value === 'hospital') {
    return [
      { label: 'ID', value: p.id },
      { label: 'User ID', value: p.user_id },
      { label: 'Hospital Name', value: p.hospital_name },
      { label: 'Registration Number', value: p.registration_number },
      { label: 'City', value: p.city },
      { label: 'State', value: p.state },
      { label: 'Phone', value: p.phone },
      { label: 'Email', value: p.email },
      { label: 'Website', value: p.website || '-' },
      { label: 'Bed Capacity', value: p.bed_capacity ?? '-' },
      { label: 'Specializations', value: (p.specializations || []).join(', ') || '-' },
      { label: 'Verified', value: p.is_verified ? 'Yes' : 'No' },
      { label: 'Created At', value: p.created_at ? new Date(p.created_at).toLocaleString() : '-' },
    ]
  }

  return []
})

async function submitAddDonor() {
  addDonorLoading.value = true
  addDonorMsg.value = ''
  addDonorError.value = false
  try {
    await api.post('/donor', {
      full_name: donorForm.value.full_name,
      age: donorForm.value.age,
      blood_group: donorForm.value.blood_group,
      location: donorForm.value.location,
      organs_selected: donorForm.value.organs_selected,
      medical_history: donorForm.value.medical_history,
      emergency_contact: donorForm.value.emergency_contact,
    })
    addDonorMsg.value = 'Donor added successfully!'
    donorForm.value = {
      full_name: '',
      age: null,
      blood_group: '',
      location: '',
      organs_selected: [],
      medical_history: '',
      emergency_contact: '',
    }
    await loadDonors()
  } catch (err) {
    addDonorError.value = true
    addDonorMsg.value = err.response?.data?.detail || 'Failed to add donor'
  } finally {
    addDonorLoading.value = false
  }
}

async function deleteDonor(id) {
  if (confirm('Are you sure you want to delete this donor?')) {
    try {
      await api.delete(`/donor/${id}`)
      await loadDonors()
    } catch (err) {
      alert('Failed to delete donor: ' + (err.response?.data?.detail || err.message))
    }
  }
}

async function triggerTraining() {
  trainMsg.value = ''
  const res = await api.post('/ml/train')
  trainingStatus.value = 'running'
  trainMsg.value = res.data.message
  // Poll status
  const poll = setInterval(async () => {
    try {
      const r = await api.get('/ml/training-status')
      trainingStatus.value = r.data.status
      if (r.data.last_trained) lastTrained.value = r.data.last_trained
      if (r.data.status !== 'running') clearInterval(poll)
    } catch { clearInterval(poll) }
  }, 3000)
}

async function submitContent() {
  contentLoading.value = true
  contentMsg.value = ''
  try {
    await api.post('/admin/awareness', contentForm.value)
    contentMsg.value = 'Content published successfully!'
    contentForm.value = { title: '', type: 'myth', content: '' }
  } finally {
    contentLoading.value = false
  }
}

async function loadSystemLogs() {
  logsLoading.value = true
  try {
    const [chatRes, modelRes] = await Promise.all([
      api.get('/admin/chat-logs'),
      api.get('/admin/model-versions')
    ])
    console.log(modelRes.data)
    chatLogs.value = chatRes.data.logs
    modelVersions.value = modelRes.data.versions
  } 
  catch (err) {
    console.error(err)
  } finally {
    logsLoading.value = false
  }
}


function viewRecipientDetails(recipient) {
  selectedRecipient.value = recipient
  recipientDetailsModal.value = true
}

function closeRecipientDetails() {
  recipientDetailsModal.value = false
  selectedRecipient.value = null
}

async function approveRecipientVerification(recipientId) {
  if (!confirm('Are you sure you want to verify and approve this recipient?')) return
  try {
    await api.post(`/recipient/admin/${recipientId}/approve`, { reviewer_notes: 'Approved by admin' })
    closeRecipientDetails()
    alert('Recipient verified successfully!')
  } catch (error) {
    alert('Error approving recipient: ' + (error.response?.data?.detail || error.message))
  }
}

function openRejectRecipientModal(recipientId) {
  rejectingRecipientId.value = recipientId
  rejectRecipientModal.value = true
  rejectRecipientReason.value = ''
}

function cancelRejectRecipient() {
  rejectRecipientModal.value = false
  rejectRecipientReason.value = ''
  rejectingRecipientId.value = null
}

async function confirmRejectRecipient() {
  if (!rejectRecipientReason.value.trim()) {
    alert('Please provide a rejection reason')
    return
  }
  try {
    await api.post(`/recipient/admin/${rejectingRecipientId.value}/reject`, {
      reviewer_notes: rejectRecipientReason.value
    })
    cancelRejectRecipient()
    alert('Recipient rejected successfully!')
  } catch (error) {
    alert('Error rejecting recipient: ' + (error.response?.data?.detail || error.message))
  }
}

function formatDate(dateString) {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

watch(activeTab, (tab) => {
  if (tab === 'analytics' && !analytics.value) loadAnalytics()
  if (tab === 'donors') loadDonors()
  // if (tab === 'pending-verification') loadPendingRecipients()
  if (tab === 'recipients') {
    loadRecipients()
    if (!hospitals.value.length) loadHospitals()
  }
  if (tab === 'hospitals') loadHospitals()
  if (tab === 'system') loadSystemLogs()
})

watch(growthMonthOptions, (options) => {
  if (!options.length) return
  const allowed = options.map((o) => o.value)
  if (!allowed.includes(selectedGrowthMonth.value)) {
    selectedGrowthMonth.value = allowed[0]
  }
}, { immediate: true })

watch(statusFilter, loadDonors)
watch(recipientStatusFilter, loadRecipients)
watch(hospitalVerifiedFilter, loadHospitals)

onMounted(loadAnalytics)
</script>

<style scoped>
.tabs { display: flex; gap: 0; margin-bottom: 32px; border: 2px solid #000; border-radius: 4px; overflow: hidden; width: fit-content; box-shadow: var(--shadow-sm); }
.tab-btn {
  padding: 10px 22px; border: none; background: #fff; font-size: 13px;
  font-weight: 700; cursor: pointer; color: var(--text-muted);
  border-right: 2px solid #000;
  transition: var(--transition); font-family: var(--font); letter-spacing: 0.02em; white-space: nowrap;
}
.tab-btn:last-child { border-right: none; }
.tab-btn.active { background: var(--accent); color: #000; }
.tab-btn:hover:not(.active) { background: var(--bg-subtle); color: var(--text); }
.table-wrapper { overflow-x: auto; }
.filter-select {
  padding: 9px 14px; border: 2px solid #000;
  border-radius: 4px; font-size: 13px; font-family: var(--font);
  color: var(--text); background: #fff; outline: none;
  box-shadow: 2px 2px 0 #000; transition: transform var(--transition), box-shadow var(--transition);
}
.filter-select:focus { box-shadow: 3px 3px 0 #000; }
.action-btns { display: flex; gap: 6px; flex-wrap: wrap; }
.ml-status-box {
  display: flex; align-items: center; gap: 22px;
  padding: 22px 26px; background: #fff;
  border: 2px solid #000; border-radius: 6px; margin-bottom: 24px;
  box-shadow: var(--shadow-md);
}
.ml-status-icon { font-size: 44px; flex-shrink: 0; }
.ml-status-text { font-size: 17px; font-weight: 800; margin-bottom: 4px; color: var(--text); }
.ml-last { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.ml-note { margin-top: 18px; font-size: 13px; color: var(--text-muted); line-height: 1.6; font-weight: 500; }

.truncate { max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.table-sm th, .table-sm td { padding: 8px 12px; font-size: 12px; }

/* Donor Form Styles */
.form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px; }
.checkbox-group { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 8px; }
.checkbox-group label { display: flex; align-items: center; gap: 6px; font-weight: 500; cursor: pointer; }
.checkbox-group input[type="checkbox"] { cursor: pointer; }
.donor-count { margin-left: 16px; font-size: 13px; color: var(--text-muted); font-weight: 500; background: var(--bg-subtle); padding: 4px 10px; border-radius: 4px; }
.btn-danger { background: #dc2626; color: #fff; border: 2px solid #dc2626; }
.btn-danger:hover { background: #b91c1c; border-color: #b91c1c; }

/* Modal Styles */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-dialog { background: #fff; border: 2px solid #000; border-radius: 8px; box-shadow: 0 20px 25px rgba(0,0,0,0.15); max-width: 500px; width: 90%; }
.modal-header { padding: 20px; border-bottom: 2px solid #000; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 18px; font-weight: 700; }
.modal-close { background: none; border: none; font-size: 24px; cursor: pointer; padding: 0; color: var(--text-muted); }
.modal-close:hover { color: var(--text); }
.modal-body { padding: 20px; }
.modal-footer { padding: 16px 20px; border-top: 2px solid #000; display: flex; gap: 10px; justify-content: flex-end; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.page-info {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}

.analytics-kpi-grid,
.analytics-charts-grid {
  align-items: stretch;
}

.analytics-kpi-grid > *,
.analytics-charts-grid > * {
  min-width: 0;
}

.chart-card {
  min-width: 0;
  overflow: hidden;
}

.chart-card canvas {
  max-width: 100%;
}

.analytics-filters {
  min-width: 0;
}

.analytics-filters .filter-select,
.analytics-filters input {
  min-width: 0;
}

@media (max-width: 1100px) {
  .analytics-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .analytics-charts-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .analytics-kpi-grid {
    grid-template-columns: 1fr;
  }

  .card-header {
    gap: 8px;
  }

  .analytics-filters {
    width: 100%;
    display: grid !important;
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .analytics-filters .filter-select,
  .analytics-filters input,
  .analytics-filters .btn {
    width: 100%;
  }

  .pagination {
    justify-content: center;
  }

  .table-wrapper {
    -webkit-overflow-scrolling: touch;
  }
}

</style>
