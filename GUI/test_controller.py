from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np
import math

class testController(QObject):
    autoStepStarted = pyqtSignal()
    autoStepFinished = pyqtSignal()
    homingFinished = pyqtSignal()
    nextStep = pyqtSignal(int)
    logMsg = pyqtSignal(str)

    def automatic_parameters(self, minFlow:int, maxFlow:int):
        self.logMsg.emit(f"Limites recividos: Qmin={minFlow}; Qmax={maxFlow}")
        maxTargetTheo = round(maxFlow,-3)
        addFirstPoint = None
        print(f"maxFlow = {maxFlow}; maxTargetTheo = {maxTargetTheo}")
        if maxFlow >= maxTargetTheo:
            maxTarget = maxTargetTheo
            print("maxFlow > maxTargetTheo")
        else:
            maxTarget = maxFlow
            print("maxFlow < maxTargetTheo")
        print(f"maxTarget = {maxTarget}")
        floor500 = math.floor(maxTarget/500)*500
        print(f"rounder500 = {floor500}")
        if maxTarget-floor500 > 250:
            addFirstPoint = maxFlow
            print(f"Se adiciona el primer punto: {addFirstPoint}")
        maxTarget = floor500

        if maxTarget <= 8000:
            print("Q < 8000 L/h")
            self.targets = np.arange(maxTarget,-1,-500)
        elif maxTarget <= 14000:
            print("8000 < Q < 14000 L/h")
            floor1000 = math.floor(maxTarget/1000)*1000
            print(f"second target: {floor1000}")
            target1000 = np.arange(floor1000,5000,-1000)
            target500 = np.arange(5500,-1,-500)
            self.targets = np.concatenate((target1000,target500))
        else:
            print("Q > 14000 L/h")
            floor1000 = math.floor(maxTarget/1000)*1000
            if maxTarget == floor1000:
                self.targets = np.arange(maxTarget,-1,-1000)
            else:
                target1000 = np.arange(floor1000,-1,-1000)
                self.targets = np.insert(target1000,0,maxTarget)
            
        if addFirstPoint:
            print("entra en addFirstPoint")
            self.targets = np.insert(self.targets,0,addFirstPoint)
        self.currentIndex = 0
        self.homingFinished.emit()
        self.logMsg.emit(f"targets: {self.targets}")

    def next_step(self):
        if self.currentIndex >= len(self.targets):
            self.logMsg.emit("Adquisicion finalizada")
            self.autoStepFinished.emit()
            return
        target = self.targets[self.currentIndex]
        self.currentIndex += 1
        if target == 0:
            self.logMsg.emit("Caudal 0, cerrar válvula a mano")
        else:
            self.logMsg.emit("TestController: next target="+str(target)+" L/h")
        self.nextStep.emit(target)
