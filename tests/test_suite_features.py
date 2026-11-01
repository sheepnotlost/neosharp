from copy import deepcopy
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from app import App
from appearance import SKINS, stop_sound
from construction_runner import ConstructionRunner
from macro_core import Control, Interrupted, default_profile, load_profile, save_profile, validate_profile
from test_construction import ConstructionBackend, ConstructionDetector
from test_macro import FakeClock
from vision import Anchor, Detector


class SlotThresholdTests(unittest.TestCase):
    def test_qualifying_result_stops_before_loading_another_blueprint(self):
        profile=default_profile();profile["operation"]="construction";profile["client_size"]=[1920,1080]
        profile["construction"]={"recipe":"holy_heal","available":4,"count":0,"count_slots":False,"stop_at_slots":4}
        clock=FakeClock();backend=ConstructionBackend(clock,"holy_heal",4)
        backend.settle_result=True;backend.result_slots=[0,2,4,5]
        events=[]
        runner=ConstructionRunner(profile,backend,Control(),lambda k,v:events.append((k,v)),clock.clock,clock.sleep,
                                  detector=ConstructionDetector())
        runner.run()
        self.assertFalse([e for e in events if e[0]=="error"],events)
        self.assertEqual(runner.completed,3)
        self.assertEqual(len(backend.transfers),3)
        self.assertEqual(len(backend.starts),3)
        self.assertEqual(backend.available,1)
        self.assertTrue(backend.output)
        self.assertIn("4 slots",[v for k,v in events if k=="done"][-1])

    def test_invalid_threshold_and_counter_type_are_rejected(self):
        for key,value in (("stop_at_slots",6),("stop_at_slots",-1),("stop_at_slots",True),("count_slots","yes")):
            profile=default_profile();profile["construction"][key]=value
            with self.assertRaises(ValueError):validate_profile(profile,require_ready=False)


class AppearanceUiTests(unittest.TestCase):
    def test_basic_restores_original_layouts_and_fonts_after_other_skins(self):
        from tkinter import ttk
        from appearance import apply_skin
        from skin_chrome import TREATMENTS
        class NoInput:
            def release_all(self):pass
        with tempfile.TemporaryDirectory() as folder,patch("app.stop_sound"):
            root=tk.Tk();root.withdraw();app=App(root,Path(folder)/"profile.json",NoInput())
            try:
                style=ttk.Style(root)
                apply_skin(root,"basic",app.heading)
                names=("TLabelframe","TButton","TEntry","TCombobox","TNotebook.Tab")
                baseline={name:style.layout(name) for name in names}
                fonts={name:str(style.lookup(name,"font")) for name in ("TButton","TLabelframe.Label")}
                self.assertEqual(len(TREATMENTS),14)                       # every skin but Basic, Dead Sector included
                for key in TREATMENTS:
                    apply_skin(root,key,app.heading)
                    self.assertIn(f"Macro.{key}.panel",str(style.layout("TLabelframe")))
                    self.assertEqual(app.heading._titlebar.winfo_manager(),"grid")      # the Winamp title bar
                    self.assertEqual(app.heading.winfo_manager(),"")
                    self.assertEqual(app.start_button.cget("style"),"Start.TButton")
                apply_skin(root,"basic",app.heading)
                self.assertEqual({name:style.layout(name) for name in names},baseline)
                self.assertEqual({name:str(style.lookup(name,"font")) for name in fonts},fonts)
                self.assertFalse(app.heading.cget("image"))
                self.assertEqual(app.heading.winfo_manager(),"grid")
                self.assertEqual(app.heading._titlebar.winfo_manager(),"")
                self.assertEqual(app.start_button.cget("style"),"TButton")
            finally:app.close()

    def test_skin_artwork_never_hides_text_or_leaves_stray_marks(self):
        # Live (28 Oct): every button in the 13 drawn skins showed no text (a "border" layout node is drawn after
        # its children, so the image covered the label), and corner details repeated across panels as stray marks.
        from tkinter import ttk
        from appearance import SKINS, apply_skin
        from skin_chrome import TREATMENTS, BORDER, surface
        root=tk.Tk();root.withdraw()
        try:
            style=ttk.Style(root);style.theme_use("clam")
            for key,treatment in TREATMENTS.items():
                apply_skin(root,key,None)
                with self.subTest(skin=key):
                    for name in ("TButton","TNotebook.Tab","TLabelframe","TEntry","TCombobox"):
                        def nodes(layout):
                            for element,options in layout:
                                yield element,options
                                yield from nodes(options.get("children",[]))
                        image=[o for e,o in nodes(style.layout(name)) if e.startswith(f"Macro.{key}.")]
                        self.assertEqual(len(image),1,name)
                        self.assertNotIn("border",image[0],name)
                    left,top,right,bottom=BORDER
                    for role in ("panel","button","field","tab"):
                        picture=surface(root,SKINS[key],treatment["kind"],role)
                        w,h=picture.width(),picture.height()
                        pixel=lambda x,y:picture.get(x,y)
                        for y in list(range(top))+list(range(h-bottom,h)):            # edges: the same all along
                            self.assertEqual({pixel(x,y) for x in range(left,w-right)}.__len__(),1,(role,y))
                        for x in list(range(left))+list(range(w-right,w)):
                            self.assertEqual({pixel(x,y) for y in range(top,h-bottom)}.__len__(),1,(role,x))
                        self.assertEqual(len({pixel(x,y) for x in range(left,w-right,7) for y in range(top,h-bottom,5)}),1,role)
        finally:root.destroy()

    def test_all_ten_skins_preserve_jobs_and_preferences_persist(self):
        class NoInput:
            def release_all(self):pass
        with tempfile.TemporaryDirectory() as folder,patch("app.stop_sound"):
            root=tk.Tk();root.withdraw();app=App(root,Path(folder)/"profile.json",NoInput())
            try:
                self.assertEqual(len(SKINS),15);self.assertIn("basic",SKINS)
                app.tabs.select(app.construction_tab)
                before=app.collect();before.pop("preferences")
                for key,skin in SKINS.items():
                    app.skin_var.set(skin["name"]);app.save_preferences()
                    current=app.collect();current.pop("preferences")
                    self.assertEqual(current,before)
                    self.assertEqual(load_profile(app.profile_path)["preferences"]["skin"],key)
                app.tabs.select(app.research_tab)
                profile=app.collect();validate_profile(profile,require_ready=False)
                self.assertEqual(profile["operation"],"tech_parts")
            finally:app.close()

    def test_optional_stop_sound_is_deduplicated_per_batch(self):
        class NoInput:
            def release_all(self):pass
        with tempfile.TemporaryDirectory() as folder,patch("app.stop_sound") as sound:
            root=tk.Tk();root.withdraw();app=App(root,Path(folder)/"profile.json",NoInput())
            try:
                app.stop_sound_var.set(True)
                app.events.put(("error","Game lost focus"));app.poll()
                app.events.put(("done","Already ended"));app.poll()
                sound.assert_called_once_with(True)
                app._stop_sound_played=False
                app.events.put(("done","Slot target reached"));app.poll()
                self.assertEqual(sound.call_count,2)
            finally:app.close()
            self.assertEqual(sound.call_count,2)

    def test_disabled_audio_never_calls_windows_playback(self):
        with patch("winsound.PlaySound") as sound:
            self.assertFalse(stop_sound(False))
            sound.assert_not_called()
