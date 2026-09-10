#pragma once
#include <gtkmm.h>
#include <gtk-layer-shell.h>
#include <json/json.h>
#include <algorithm>
#include <array>
#include <ctime>
#include <fstream>
#include <functional>
#include <iomanip>
#include <sstream>
#include <vector>

namespace waybar::modules {

// Independent layer surface: never affects the bar size or exclusive zone.
class DesktopCalendar : public sigc::trackable {
  Gtk::Widget& anchor_;
  Gtk::Window popup_;
  Gtk::Box body_{Gtk::ORIENTATION_VERTICAL, 12};
  Gtk::Box header_{Gtk::ORIENTATION_HORIZONTAL, 8};
  Gtk::Grid grid_;
  Gtk::Label title_, detail_, coverage_, legend_;
  Gtk::Button previous_{"‹"}, next_{"›"}, today_{"Today"}, close_{"×"};
  Json::Value data_;
  sigc::connection close_timer_, open_timer_;
  std::vector<sigc::connection> connections_;
  int year_ = 0, month_ = 0, cell_ = 64;
  bool over_clock_ = false, over_popup_ = false, pinned_ = false;
  std::string today_key_;

  static std::tm now() {
    const auto stamp = std::time(nullptr);
    std::tm result{};
    localtime_r(&stamp, &result);
    return result;
  }
  static std::string key(int year, int month, int day) {
    std::ostringstream s;
    s << year << '-' << std::setfill('0') << std::setw(2) << month << '-' << std::setw(2) << day;
    return s.str();
  }
  void cancel_close() { close_timer_.disconnect(); }
  void schedule_close() {
    cancel_close();
    close_timer_ = Glib::signal_timeout().connect([this] {
      if (!over_clock_ && !over_popup_ && !pinned_) popup_.hide();
      return false;
    }, 650);
  }
  void reset_month() {
    const auto t = now();
    year_ = t.tm_year + 1900;
    month_ = t.tm_mon + 1;
    today_key_ = key(year_, month_, t.tm_mday);
  }
  void open() {
    cancel_close();
    if (!popup_.get_visible()) {
      reset_month();
      auto display = anchor_.get_display();
      auto monitor = display->get_monitor_at_window(anchor_.get_window());
      if (monitor) {
        gtk_layer_set_monitor(popup_.gobj(), monitor->gobj());
        auto* parent = dynamic_cast<Gtk::Window*>(anchor_.get_toplevel());
        int margin = parent ? parent->get_allocated_height() : 34;
        gtk_layer_set_margin(popup_.gobj(), GTK_LAYER_SHELL_EDGE_TOP, margin);
        Gdk::Rectangle area;
        monitor->get_workarea(area);
        // Logical pixels: GTK also applies the monitor's HiDPI scale.
        cell_ = std::clamp(std::min(area.get_height() / 20, (area.get_width() - 64) / 7), 36, 72);
      }
      render();
      popup_.show_all();

    }
  }
  void shift(int amount) {
    month_ += amount;
    if (month_ == 0) { month_ = 12; --year_; }
    if (month_ == 13) { month_ = 1; ++year_; }
    render();
  }
  void render() {
    for (auto* child : grid_.get_children()) grid_.remove(*child);
    static const std::array<const char*, 12> months = {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"};
    title_.set_text(std::string(months[month_ - 1]) + " " + std::to_string(year_));
    const auto t = now();
    today_key_ = key(t.tm_year + 1900, t.tm_mon + 1, t.tm_mday);
    std::tm first{};
    first.tm_year = year_ - 1900; first.tm_mon = month_ - 1; first.tm_mday = 1;
    first.tm_hour = 12; first.tm_isdst = -1;
    std::mktime(&first);
    const int offset = (first.tm_wday + 6) % 7;
    const bool leap = year_ % 4 == 0 && (year_ % 100 != 0 || year_ % 400 == 0);
    const std::array<int, 12> lengths = {31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    const std::array<const char*, 7> weekdays = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"};
    for (int col = 0; col < 7; ++col) {
      auto* label = Gtk::manage(new Gtk::Label(weekdays[col]));
      label->get_style_context()->add_class("calendar-weekday");
      grid_.attach(*label, col, 0, 1, 1);
    }
    for (int slot = 0; slot < ((offset + lengths[month_ - 1] + 6) / 7) * 7; ++slot) {
      int day = slot - offset + 1;
      auto* area = Gtk::manage(new Gtk::DrawingArea());
      area->set_size_request(cell_, cell_);
      grid_.attach(*area, slot % 7, slot / 7 + 1, 1, 1);
      if (day < 1 || day > lengths[month_ - 1]) continue;
      const auto date_key = key(year_, month_, day);
      bool is_today = date_key == today_key_;
      std::array<bool, 3> marked{};
      std::string description = date_key + (is_today ? " · Today" : "");
      for (const auto& entry : data_["dates"][date_key]) {
        const auto region = entry["region"].asString();
        int index = region == "cat" ? 0 : region == "ar" ? 1 : 2;
        marked[index] = true;
        const std::array<const char*, 3> regions = {"Catalunya / Barcelona", "Argentina", "USA (federal)"};
        description += "\n" + std::string(regions[index]) + ": " + entry["name"].asString();
      }
      if (!marked[0] && !marked[1] && !marked[2]) description += "\nNo listed holidays";
      area->set_has_tooltip(true);
      area->set_can_focus(true);
      area->get_accessible()->set_name(description);
      area->add_events(Gdk::ENTER_NOTIFY_MASK | Gdk::LEAVE_NOTIFY_MASK | Gdk::BUTTON_PRESS_MASK | Gdk::POINTER_MOTION_MASK);
      area->signal_motion_notify_event().connect([this, description, area](GdkEventMotion*) {
        detail_.set_text(description); area->set_state_flags(Gtk::STATE_FLAG_PRELIGHT); area->queue_draw(); return false;
      });
      area->signal_query_tooltip().connect([this, description](int, int, bool, const Glib::RefPtr<Gtk::Tooltip>& tooltip) {
        detail_.set_text(description); tooltip->set_text(description); return true;
      });
      area->signal_enter_notify_event().connect([this, description, area](GdkEventCrossing*) {
        detail_.set_text(description); area->set_state_flags(Gtk::STATE_FLAG_PRELIGHT); area->queue_draw(); return false;
      });
      area->signal_leave_notify_event().connect([area](GdkEventCrossing*) {
        area->unset_state_flags(Gtk::STATE_FLAG_PRELIGHT); area->queue_draw(); return false;
      });
      area->signal_focus_in_event().connect([this, description](GdkEventFocus*) { detail_.set_text(description); return false; });
      area->signal_button_press_event().connect([this, description](GdkEventButton*) { detail_.set_text(description); return true; });
      area->signal_draw().connect([area, day, marked, is_today, weekend = slot % 7 >= 5](const Cairo::RefPtr<Cairo::Context>& cr) {
        const double width = area->get_allocated_width(), height = area->get_allocated_height();
        if ((area->get_state_flags() & Gtk::STATE_FLAG_PRELIGHT) != 0) {
          cr->set_source_rgba(0.60, 0.70, 0.85, 0.14); cr->rectangle(3, 3, width-6, height-6); cr->fill();
        }
        const std::array<std::array<double, 3>, 3> colors = {{{1.0, 0.62, 0.27}, {0.42, 0.81, 1.0}, {0.76, 0.57, 1.0}}};
        double inset = 4;
        for (int i = 0; i < 3; ++i) if (marked[i]) {
          cr->set_source_rgb(colors[i][0], colors[i][1], colors[i][2]); cr->set_line_width(2);
          cr->rectangle(inset, inset, width-2*inset, height-2*inset); cr->stroke(); inset += 3;
        }
        if (is_today) {
          cr->set_source_rgba(0.90, 0.95, 1.0, 0.12); cr->rectangle(inset, inset, width-2*inset, height-2*inset); cr->fill();
          cr->set_source_rgb(0.90, 0.95, 1.0); cr->set_line_width(2);
          cr->rectangle(inset, inset, width-2*inset, height-2*inset); cr->stroke();
        }
        auto layout = area->create_pango_layout(std::to_string(day));
        Pango::FontDescription font("Inter");
        font.set_absolute_size(std::clamp(height * .31, 14.0, 22.0) * Pango::SCALE);
        font.set_weight(is_today ? Pango::WEIGHT_BOLD : Pango::WEIGHT_NORMAL);
        layout->set_font_description(font);
        int tw, th; layout->get_pixel_size(tw, th);
        cr->set_source_rgb(weekend && !is_today ? .67 : .92, weekend && !is_today ? .71 : .94, weekend && !is_today ? .78 : .98);
        cr->move_to((width-tw)/2, (height-th)/2); layout->show_in_cairo_context(cr);
        return true;
      });
    }
    detail_.set_size_request(cell_ * 7, 90);
    detail_.set_max_width_chars(54);
    detail_.set_text("Hover a day to see holidays\nClick the clock to keep the calendar open");
    bool in_range = year_ >= data_.get("first_year", 2020).asInt() && year_ <= data_.get("last_year", 2040).asInt();
    coverage_.set_text(!in_range ? "Holiday data unavailable for this year" : year_ == 2026 ? "Barcelona local dates verified · 2026" : year_ == 2027 ? "Barcelona verified · Argentina special dates may change" : "Rule-based dates · Barcelona local dates not loaded");
    grid_.show_all();
  }
 public:
  DesktopCalendar(Gtk::Widget& anchor, const std::string& path) : anchor_(anchor) {
    std::ifstream input(path);
    if (!(input >> data_)) throw std::runtime_error("Cannot read calendar holiday data");
    popup_.set_name("desktop-calendar");
    popup_.set_decorated(false);
    popup_.set_resizable(false);
    gtk_layer_init_for_window(popup_.gobj());
    gtk_layer_set_namespace(popup_.gobj(), "waybar-calendar");
    gtk_layer_set_layer(popup_.gobj(), GTK_LAYER_SHELL_LAYER_OVERLAY);
    gtk_layer_set_anchor(popup_.gobj(), GTK_LAYER_SHELL_EDGE_TOP, true);
    gtk_layer_set_exclusive_zone(popup_.gobj(), -1);
    gtk_layer_set_keyboard_mode(popup_.gobj(), GTK_LAYER_SHELL_KEYBOARD_MODE_ON_DEMAND);
    popup_.add(body_);
    body_.set_margin_start(18); body_.set_margin_end(18); body_.set_margin_top(14); body_.set_margin_bottom(14);
    header_.pack_start(previous_, false, false); header_.pack_start(title_, true, true);
    header_.pack_start(next_, false, false); header_.pack_start(today_, false, false); header_.pack_start(close_, false, false);
    body_.pack_start(header_, false, false); body_.pack_start(grid_, false, false);
    legend_.set_markup("<span foreground='#ff9e45'>■ Catalunya / Barcelona</span>   <span foreground='#6bcfff'>■ Argentina</span>   <span foreground='#c292ff'>■ USA</span>");
    body_.pack_start(legend_, false, false);
    detail_.set_line_wrap(true); detail_.set_xalign(0); detail_.set_yalign(0);
    body_.pack_start(detail_, false, false); body_.pack_start(coverage_, false, false);
    coverage_.get_style_context()->add_class("calendar-coverage");
    title_.get_style_context()->add_class("calendar-title");
    previous_.set_tooltip_text("Previous month"); next_.set_tooltip_text("Next month"); close_.set_tooltip_text("Close calendar");
    previous_.signal_clicked().connect([this] { shift(-1); });
    next_.signal_clicked().connect([this] { shift(1); });
    today_.signal_clicked().connect([this] { reset_month(); render(); });
    close_.signal_clicked().connect([this] { pinned_ = false; popup_.hide(); });
    popup_.signal_key_press_event().connect([this](GdkEventKey* e) {
      if (e->keyval == GDK_KEY_Escape) { pinned_ = false; popup_.hide(); return true; } return false;
    });
    popup_.add_events(Gdk::ENTER_NOTIFY_MASK | Gdk::LEAVE_NOTIFY_MASK);
    popup_.signal_enter_notify_event().connect([this](GdkEventCrossing*) { over_popup_ = true; cancel_close(); return false; });
    popup_.signal_leave_notify_event().connect([this](GdkEventCrossing* e) {
      if (e->detail != GDK_NOTIFY_INFERIOR) { over_popup_ = false; schedule_close(); } return false;
    });
    popup_.signal_hide().connect([this] { over_popup_ = false; pinned_ = false; });
    connections_.push_back(anchor_.signal_enter_notify_event().connect([this](GdkEventCrossing*) {
      over_clock_ = true; cancel_close(); open_timer_.disconnect();
      open_timer_ = Glib::signal_timeout().connect([this] { if (over_clock_) open(); return false; }, 160);
      return false;
    }));
    connections_.push_back(anchor_.signal_leave_notify_event().connect([this](GdkEventCrossing* e) {
      if (e->detail != GDK_NOTIFY_INFERIOR) { over_clock_ = false; open_timer_.disconnect(); schedule_close(); } return false;
    }));
    anchor_.add_events(Gdk::BUTTON_PRESS_MASK);
    connections_.push_back(anchor_.signal_button_press_event().connect([this](GdkEventButton* e) {
      if (e->button != 1) return false;
      pinned_ = !pinned_;
      if (pinned_) open(); else popup_.hide();
      return true;
    }, false));
  }
  void refresh_today() {
    if (!popup_.get_visible()) return;
    const auto t = now();
    if (today_key_ != key(t.tm_year + 1900, t.tm_mon + 1, t.tm_mday)) render();
  }
  ~DesktopCalendar() {
    open_timer_.disconnect(); close_timer_.disconnect();
    for (auto& connection : connections_) connection.disconnect();
  }
};
}  // namespace waybar::modules
