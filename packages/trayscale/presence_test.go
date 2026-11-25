package tsutil

import (
	"testing"
	"time"

	"tailscale.com/ipn/ipnstate"
	"tailscale.com/tailcfg"
	"tailscale.com/types/key"
	"tailscale.com/types/netmap"
)

func TestPeerPresenceUsesLiveStatusWithoutMutatingSnapshots(t *testing.T) {
	oldTime := time.Unix(100, 0)
	newTime := time.Unix(200, 0)
	offline := false
	peer := (&tailcfg.Node{StableID: "peer", Name: "peer.example.", Online: &offline, LastSeen: &oldTime}).View()
	original := &IPNStatus{Peers: map[tailcfg.StableNodeID]tailcfg.NodeView{"peer": peer}}
	current := original.copy()
	live := &ipnstate.PeerStatus{ID: "peer", Online: true, LastSeen: newTime}
	status := &ipnstate.Status{BackendState: "Running", Peer: map[key.NodePublic]*ipnstate.PeerStatus{{}: live}}
	current.applyPeerPresence(status)
	if !current.Peers["peer"].Online().Get() || !current.Peers["peer"].LastSeen().Get().Equal(newTime) {
		t.Fatal("live presence did not replace stale network-map values")
	}
	if original.Peers["peer"].Online().Get() || !peer.LastSeen().Get().Equal(oldTime) {
		t.Fatal("refresh mutated a previously published snapshot")
	}
	if current.Peers["peer"].Name() != peer.Name() {
		t.Fatal("refresh lost network-map metadata")
	}
	previous := current.copy()
	live.Online = false
	current.applyPeerPresence(status)
	if current.Peers["peer"].Online().Get() || !previous.Peers["peer"].Online().Get() {
		t.Fatal("online-to-offline transition was not isolated to the new snapshot")
	}
}

func TestPeerPresenceIgnoresUnrelatedOrUnavailableStatus(t *testing.T) {
	online := true
	peer := (&tailcfg.Node{StableID: "peer", Online: &online}).View()
	s := &IPNStatus{
		NetMap: &netmap.NetworkMap{SelfNode: (&tailcfg.Node{StableID: "self"}).View()},
		Peers: map[tailcfg.StableNodeID]tailcfg.NodeView{"peer": peer},
	}
	for _, status := range []*ipnstate.Status{
		nil,
		{BackendState: "Stopped"},
		{BackendState: "Running", Self: &ipnstate.PeerStatus{ID: "other-profile"},
			Peer: map[key.NodePublic]*ipnstate.PeerStatus{{}: {ID: "peer", Online: false}}},
		{BackendState: "Running", Self: &ipnstate.PeerStatus{ID: "self"},
			Peer: map[key.NodePublic]*ipnstate.PeerStatus{{}: nil}},
		{BackendState: "Running", Self: &ipnstate.PeerStatus{ID: "self"},
			Peer: map[key.NodePublic]*ipnstate.PeerStatus{{}: {ID: "removed-peer"}}},
	} {
		s.applyPeerPresence(status)
		if len(s.Peers) != 1 || !s.Peers["peer"].Online().Get() {
			t.Fatal("unrelated status changed existing peers")
		}
	}
}
