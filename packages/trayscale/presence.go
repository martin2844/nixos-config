package tsutil

import (
	"context"
	"log/slog"
	"time"

	"tailscale.com/ipn/ipnstate"
)

// publishIPN owns the published snapshot. NetMap can retain old Online and
// LastSeen values even when the daemon's status API has newer peer presence.
// Refresh on notifications and while idle, without mutating shared NodeViews.
func (p *Poller) publishIPN(ctx context.Context, updates <-chan *IPNStatus) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	var current *IPNStatus
	var get chan *IPNStatus
	for {
		select {
		case <-ctx.Done():
			return
		case current = <-updates:
		case <-ticker.C:
			if current == nil || !current.Online() {
				continue
			}
		case get <- current:
			continue
		}

		current = current.copy()
		if current.Online() {
			queryCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
			status, err := GetStatus(queryCtx)
			cancel()
			if err != nil {
				if ctx.Err() != nil {
					return
				}
				slog.Warn("refresh peer presence", "err", err)
			} else {
				current.applyPeerPresence(status)
			}
		}

		get = p.getIPN
		p.New(current)
		select {
		case p.nextIPN <- current:
		default:
		}
	}
}

func (s *IPNStatus) applyPeerPresence(status *ipnstate.Status) {
	if status == nil || status.BackendState != "Running" {
		return
	}
	// A profile switch may race the status request. Wait for its own NetMap.
	if s.NetMap != nil && s.NetMap.SelfNode.Valid() &&
		(status.Self == nil || status.Self.ID != s.NetMap.SelfNode.StableID()) {
		return
	}
	for _, live := range status.Peer {
		if live == nil {
			continue
		}
		peer, ok := s.Peers[live.ID]
		if !ok {
			continue
		}
		node := peer.AsStruct()
		online, lastSeen := live.Online, live.LastSeen
		node.Online = &online
		node.LastSeen = &lastSeen
		s.Peers[live.ID] = node.View()
	}
}
