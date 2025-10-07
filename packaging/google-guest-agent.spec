#  Copyright 2018 Google LLC

#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Don't build debuginfo packages.
%define debug_package %{nil}

# The only use for extra source is to build plugin manager.
%if 0%{?has_extra_source}
%define build_plugin_manager %{has_extra_source}
%endif

Name: google-guest-agent
Epoch:   1
Version: %{_version}
Release: g1%{?dist}
Summary: Google Compute Engine guest agent.
License: ASL 2.0
Url: https://cloud.google.com/compute/docs/images/guest-environment
Source0: %{name}_%{version}.orig.tar.gz

%if 0%{?build_plugin_manager}
Source1: %{name}_extra-%{version}.orig.tar.gz
%endif

Requires: google-compute-engine-oslogin >= 1:20231003
BuildArch: %{_arch}
Obsoletes: python-google-compute-engine, python3-google-compute-engine

%description
Contains the Google guest agent binary.

%prep

%if 0%{?build_plugin_manager}
%autosetup -a 1
%else
%autosetup
%endif

%build
%if 0%{?build_plugin_manager}
pushd %{name}-extra-%{version}/
  VERSION=%{version} make cmd/google_guest_agent/google_guest_agent
  VERSION=%{version} make cmd/ggactl/ggactl_plugin
  VERSION=%{version} make cmd/core_plugin/core_plugin
  VERSION=%{version} make cmd/gce_metadata_script_runner/gce_metadata_script_runner
popd
%else
for bin in google_guest_agent google_metadata_script_runner gce_workload_cert_refresh; do
  pushd "$bin"
  GOPATH=%{_gopath} CGO_ENABLED=0 %{_go} build -ldflags="-s -w -X main.version=%{_version}" -mod=readonly
  popd
done
%endif

%install
install -d "%{buildroot}/%{_docdir}/%{name}"
cp -r THIRD_PARTY_LICENSES "%buildroot/%_docdir/%name/THIRD_PARTY_LICENSES"

install -d %{buildroot}%{_bindir}
install -d %{buildroot}/usr/share/google-guest-agent
install -p -m 0644 instance_configs.cfg %{buildroot}/usr/share/google-guest-agent/instance_configs.cfg

%if 0%{?build_plugin_manager}
install -d %{buildroot}%{_exec_prefix}/lib/google/guest_agent
install -p -m 0755 %{name}-extra-%{version}/cmd/gce_metadata_script_runner/gce_metadata_script_runner %{buildroot}%{_bindir}/google_metadata_script_runner
install -p -m 0755 %{name}-extra-%{version}/cmd/google_guest_agent/google_guest_agent %{buildroot}%{_bindir}/google_guest_agent
install -p -m 0755 %{name}-extra-%{version}/cmd/ggactl/ggactl_plugin %{buildroot}%{_bindir}/ggactl
install -p -m 0755 %{name}-extra-%{version}/cmd/core_plugin/core_plugin %{buildroot}%{_exec_prefix}/lib/google/guest_agent/core_plugin
%else
install -p -m 0755 google_guest_agent/google_guest_agent %{buildroot}%{_bindir}/google_guest_agent
install -p -m 0755 google_metadata_script_runner/google_metadata_script_runner %{buildroot}%{_bindir}/google_metadata_script_runner
install -p -m 0755 gce_workload_cert_refresh/gce_workload_cert_refresh %{buildroot}%{_bindir}/gce_workload_cert_refresh
%endif

install -d %{buildroot}%{_unitdir}
install -p -m 0644 google-startup-scripts.service %{buildroot}%{_unitdir}
install -p -m 0644 google-shutdown-scripts.service %{buildroot}%{_unitdir}
%if 0%{?build_plugin_manager}
install -p -m 0644 google-guest-agent-manager.service %{buildroot}%{_unitdir}/google-guest-agent.service
%else
install -p -m 0644 google-guest-agent.service %{buildroot}%{_unitdir}
install -p -m 0644 gce-workload-cert-refresh.service %{buildroot}%{_unitdir}
install -p -m 0644 gce-workload-cert-refresh.timer %{buildroot}%{_unitdir}
%endif

install -d %{buildroot}%{_presetdir}
install -p -m 0644 90-%{name}.preset %{buildroot}%{_presetdir}/90-%{name}.preset


%files
%{_docdir}/%{name}
%defattr(-,root,root,-)
/usr/share/google-guest-agent/instance_configs.cfg
%{_bindir}/google_guest_agent

%if 0%{?build_plugin_manager}
%{_bindir}/ggactl
%{_exec_prefix}/lib/google/guest_agent/core_plugin
%else
%{_bindir}/gce_workload_cert_refresh
%endif
%{_bindir}/google_metadata_script_runner

%{_unitdir}/%{name}.service
%{_unitdir}/google-startup-scripts.service
%{_unitdir}/google-shutdown-scripts.service
%if ! 0%{?build_plugin_manager}
%{_unitdir}/gce-workload-cert-refresh.service
%{_unitdir}/gce-workload-cert-refresh.timer
%endif
%{_presetdir}/90-%{name}.preset

%post
if [ $1 -eq 1 ]; then
  # Initial installation

  # Install instance configs if not already present.
  if [ ! -f /etc/default/instance_configs.cfg ]; then
    cp -a /usr/share/google-guest-agent/instance_configs.cfg /etc/default/
  fi

  # Use enable instead of preset because preset is not supported in
  # chroots.
  systemctl enable google-guest-agent.service >/dev/null 2>&1 || :
  systemctl enable google-startup-scripts.service >/dev/null 2>&1 || :
  systemctl enable google-shutdown-scripts.service >/dev/null 2>&1 || :
  %if ! 0%{?build_plugin_manager}
  systemctl enable gce-workload-cert-refresh.timer >/dev/null 2>&1 || :
  %endif

  if [ -d /run/systemd/system ]; then
    systemctl daemon-reload >/dev/null 2>&1 || :
    %if ! 0%{?build_plugin_manager}
    systemctl start gce-workload-cert-refresh.timer >/dev/null 2>&1 || :
    %endif
  fi
else
  # Package upgrade
  if [ -d /run/systemd/system ]; then
    systemctl daemon-reload >/dev/null 2>&1 || :
    systemctl enable --now google-guest-agent.service >/dev/null 2>&1 || :
  fi

  # Only enable gce-workload-cert-refresh if not building plugin manager,
  # since plugin manager doesn't use/have this timer/service.
  %if ! 0%{?build_plugin_manager}
  systemctl enable gce-workload-cert-refresh.timer > /dev/null 2>&1 || :
  %endif
fi

%preun
if [ $1 -eq 0 ]; then
  # Package removal, not upgrade
  %if ! 0%{?build_plugin_manager}
    systemctl --no-reload disable gce-workload-cert-refresh.timer >/dev/null 2>&1 || :
  %endif
  systemctl --no-reload disable google-guest-agent.service >/dev/null 2>&1 || :
  systemctl --no-reload disable google-startup-scripts.service >/dev/null 2>&1 || :
  systemctl --no-reload disable google-shutdown-scripts.service >/dev/null 2>&1 || :
  if [ -d /run/systemd/system ]; then
    systemctl stop google-guest-agent.service >/dev/null 2>&1 || :
    # Only plugin manager needs to clean up plugins.
    %if 0%{?build_plugin_manager}
      ggactl coreplugin stop >/dev/null 2>&1 || :
      ggactl dynamic-cleanup >/dev/null 2>&1 || :
    %endif
  fi
fi

%postun
if [ $1 -eq 0 ]; then
  # Package removal, not upgrade
  if [ -f /etc/default/instance_configs.cfg ]; then
    rm /etc/default/instance_configs.cfg
  fi

  if [ -d /run/systemd/system ]; then
    systemctl daemon-reload >/dev/null 2>&1 || :
  fi
fi

