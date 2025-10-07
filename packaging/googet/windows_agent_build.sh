#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Should be run from the guest-agent directory.
# Usage:
#   ./packaging/googet/windows_agent_build.sh <version>


version=$1

GUEST_AGENT_REPO=".../google-guest-agent"

BUILD_DIR=$(pwd)

# Script expects guest-agent and google-guest-agent codebase are placed
# side-by-side within same directory and this script is executed from root of
# guest-agent codebase.
#
# If google-guest-agent exists, then build only binaries from there. Otherwise
# build from guest-agent repo.
if [[ -d "$GUEST_AGENT_REPO" ]]; then
  pushd $GUEST_AGENT_REPO
  GOOS=windows VERSION=$version make cmd/google_guest_agent/google_guest_agent
  GOOS=windows VERSION=$version make cmd/core_plugin/core_plugin
  GOOS=windows VERSION=$version make cmd/google_authorized_keys/google_authorized_keys
  GOOS=windows VERSION=$version make cmd/ggactl/ggactl_plugin

  cp cmd/google_guest_agent/google_guest_agent $BUILD_DIR/GCEWindowsAgent.exe
  cp cmd/google_authorized_keys/google_authorized_keys $BUILD_DIR/GCEAuthorizedKeysCommand.exe
  cp cmd/ggactl/ggactl_plugin $BUILD_DIR/ggact.exe
  cp cmd/core_plugin/core_plugin $BUILD_DIR/CorePlugin.exe
  popd
else
  echo "This is a placeholder file so guest agent package build without error. Package will have actual CorePlugin executable instead if both repos are cloned side-by-side." > CorePlugin.exe
  echo "This is a placeholder file so guest agent package build without error. Package will have actual ggactl executable instead if both repos are cloned side-by-side." > ggactl.exe

  # Build the packages.
  GOOS=windows /tmp/go/bin/go build -ldflags "-X main.version=$version" -mod=readonly -o GCEWindowsAgent.exe ./google_guest_agent
  GOOS=windows /tmp/go/bin/go build -ldflags "-X main.version=$version" -mod=readonly -o GCEAuthorizedKeysCommand.exe ./google_authorized_keys
fi
